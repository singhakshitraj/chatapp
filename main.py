from fastapi import FastAPI,WebSocket
from starlette.websockets import WebSocketClose,WebSocketDisconnect
from routers import auth,contacts
import time
app=FastAPI()

app.include_router(auth.router)
app.include_router(contacts.router)
