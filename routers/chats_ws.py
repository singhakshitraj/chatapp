from fastapi import WebSocket, APIRouter, Depends, status, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from sqlalchemy.orm import Session

from connections.connection_db import get_db
from connections.connection_redis import get_redis
from utils.token import JWTTokenClass
from utils.validation_models import message_validation
from connections.ws_connection_manager import ConnectionManager


router = APIRouter(
    prefix='/ws/chat/{chat_id}'
)

manager = ConnectionManager()


@router.websocket('')
async def chat(
    chat_id: str,
    websocket: WebSocket,
    db: Session = Depends(get_db),
    redis=Depends(get_redis)
):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    username = JWTTokenClass.get_user(token=token)

    if not username:
        await websocket.close(code=1008)
        return

    # Ensure participants are available even after a Redis restart by
    # falling back to the DB and repopulating Redis.
    manager.define_participants(redis=redis, chat_id=chat_id, connection=db)

    try:
        await manager.connect(websocket=websocket, username=username, chat_id=chat_id)
        while True:
            data = await websocket.receive_json()
            message = message_validation(**data)
            await manager.broadcast(
                message=message,
                db=db,
                username=username,
                chat_id=chat_id,
                redis=redis
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket=websocket, username=username, chat_id=chat_id)
    except Exception:
        manager.disconnect(websocket=websocket, username=username, chat_id=chat_id)
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=1011)
            except Exception:
                pass