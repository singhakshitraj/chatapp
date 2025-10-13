from fastapi import WebSocket,APIRouter,Depends,status,WebSocketDisconnect
from connections.connection_db import db_connect
from connections.connection_redis import get_redis
from utils.token import JWTTokenClass
from connections.ws_connection_manager import ConnectionManager
from fastapi.security import OAuth2PasswordBearer
from utils.token import JWTTokenClass
from fastapi.websockets import WebSocketState
router=APIRouter(
    prefix='/ws/chat/{chat_id}'
)

manager = ConnectionManager()
@router.websocket('')
async def chat(chat_id:str,websocket:WebSocket,connection=Depends(db_connect),redis=Depends(get_redis)):
    token = websocket.query_params.get("token")
    username=JWTTokenClass.get_user(token=token)
    if not token:
        await websocket.close(code=1008)
        return
    manager.define_participants(redis=redis,chat_id=chat_id)
    try:
        await manager.connect(websocket=websocket,username=username)
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(message=data,connection=connection,username=username,chat_id=chat_id,redis=redis)
    except WebSocketDisconnect:
        manager.disconnect(websocket=websocket, username=username)
    except Exception:
        manager.disconnect(websocket=websocket, username=username)
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=1011)
            except Exception:
                pass
        return