from fastapi import FastAPI,WebSocket,Depends
from starlette.websockets import WebSocketClose,WebSocketDisconnect
from routers import auth,contacts,chat,chats_ws
from connections.connection_redis import get_redis
app=FastAPI()

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(chat.router)
app.include_router(chats_ws.router)

@app.get('/checkredis')
def is_redis_working(redis=Depends(get_redis)):
    return {
        'contacts':redis.lrange(5,0,-1)
    }