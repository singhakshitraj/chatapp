from fastapi import WebSocket, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils.validation_models import message_validation
from websockets.exceptions import WebSocketException
from throttling_redis import RedisThrottling
from utils.exceptions import TooManyRequestError
from utils.send_email import send_email
from connections.schemas import Message
from connections.schemas import UnreadInbox
from connections.schemas import User
from connections.schemas import UserChat


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.active_users: list[str] = []
        self.participants: list[str] = []
    
    def define_participants(self, redis, chat_id: str, connection: Session):
        """
        Load participants for a chat.

        1. Try Redis (fast path).
        2. On cache miss, read from DB and repopulate Redis.
        """
        participants = redis.lrange(chat_id, 0, -1) or []

        if not participants:
            rows = (
                connection.query(UserChat.username)
                .filter(UserChat.chat_id == chat_id)
                .all()
            )
            participants = [row.username for row in rows]

            if participants:
                redis.lpush(chat_id, *participants)

        self.participants = participants
        
    async def connect(self, websocket: WebSocket, username: str):
        if username not in self.participants:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="You are not a participant."
            )
        await websocket.accept()
        self.active_users.append(username)
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, username: str):
        if username in self.active_users:
            self.active_users.remove(username)
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(
        self,
        message: message_validation,
        db: Session,
        username: str,
        chat_id: str,
        redis
    ):
        not_active = list(set(self.participants) - set(self.active_users))

        try:
            RedisThrottling.check_validity(username=username)

            # Insert the message and flush to get the generated message_id
            new_message = Message(
                chat_id=chat_id,
                message=message.message,
                sent_by=username
            )
            db.add(new_message)
            db.flush()

            if new_message.message_id is None:
                raise WebSocketException(
                    code=status.WS_1006_ABNORMAL_CLOSURE,
                    reason='DB insertion failed!'
                )

            # Bulk insert unread inbox entries for offline participants
            db.add_all([
                UnreadInbox(username=nac, message_id=new_message.message_id)
                for nac in not_active
            ])

            db.commit()

            # Broadcast to all active WebSocket connections
            for connection in self.active_connections:
                await connection.send_json({
                    'chat_id': chat_id,
                    'message': message.message,
                    'username': username
                })

        except TooManyRequestError:
            db.rollback()

            user = db.query(User).filter(User.username == username).first()
            if user is None or user.email is None:
                raise WebSocketException(
                    code=status.WS_1006_ABNORMAL_CLOSURE,
                    reason="Unable to fetch email-id's"
                )

            send_email.delay(
                to=user.email,
                subject='Notice: Temporary Throttling Applied!!'
            )

        except (SQLAlchemyError, WebSocketException):
            db.rollback()
            raise WebSocketException(
                code=status.WS_1006_ABNORMAL_CLOSURE,
                reason='An unexpected database error occurred.'
            )