from dataclasses import dataclass, field
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


@dataclass
class _ChatRoom:
    participants: list[str] = field(default_factory=list)
    active_connections: list[WebSocket] = field(default_factory=list)
    active_users: list[str] = field(default_factory=list)


class ConnectionManager:
    def __init__(self):
        self._rooms: dict[str, _ChatRoom] = {}

    def _room(self, chat_id: str) -> _ChatRoom:
        chat_id = str(chat_id)
        room = self._rooms.get(chat_id)
        if room is None:
            room = _ChatRoom()
            self._rooms[chat_id] = room
        return room

    def _cleanup_room_if_empty(self, chat_id: str) -> None:
        chat_id = str(chat_id)
        room = self._rooms.get(chat_id)
        if room is None:
            return
        if not room.active_connections and not room.active_users:
            self._rooms.pop(chat_id, None)
    
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

        self._room(chat_id).participants = participants
        
    async def connect(self, websocket: WebSocket, username: str, chat_id: str):
        room = self._room(chat_id)
        try:
            if username not in room.participants:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="You are not a participant."
                )
            await websocket.accept()
            if username not in room.active_users:
                room.active_users.append(username)
            if websocket not in room.active_connections:
                room.active_connections.append(websocket)
        except WebSocketException as e:
            await websocket.close(code=e.code, reason=e.reason)
            raise e
            print(e)
            print('WebSocketException')
        except Exception as e:
            await websocket.close(code=status.WS_1006_ABNORMAL_CLOSURE, reason='An unexpected error occurred.')
            raise e
            print(e)
            print('Exception')
    def disconnect(self, websocket: WebSocket, username: str, chat_id: str):
        chat_id = str(chat_id)
        room = self._rooms.get(chat_id)
        if room is None:
            return
        if username in room.active_users:
            room.active_users.remove(username)
        if websocket in room.active_connections:
            room.active_connections.remove(websocket)
        self._cleanup_room_if_empty(chat_id)

    async def broadcast(
        self,
        message: message_validation,
        db: Session,
        username: str,
        chat_id: str,
        redis
    ):
        room = self._room(chat_id)
        not_active = list(set(room.participants) - set(room.active_users))

        try:
            #RedisThrottling.check_validity(username=username)
            # Insert the message and flush to get the generated message_id
            new_message = Message(
                chat_id=chat_id,
                message=message.message,
                sent_by=username
            )
            db.add(new_message)
            db.flush()
            

            # Bulk insert unread inbox entries for offline participants
            db.add_all([
                UnreadInbox(username=nac, message_id=new_message.message_id)
                for nac in not_active
            ])

            db.commit()

            # Broadcast to all active WebSocket connections
            for connection in list(room.active_connections):
                await connection.send_json({
                    'chat_id': chat_id,
                    'message': message.message,
                    'username': username
                })
        except SQLAlchemyError as e:
            db.rollback()
            print("REAL DB ERROR:", repr(e))
            raise
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