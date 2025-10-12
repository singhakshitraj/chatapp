from fastapi import WebSocket,Depends,status
from utils.validation_models import message_validation
from websockets.exceptions import WebSocketException
class ConnectionManager:
    def __init__(self):
        self.active_connections:list[WebSocket]=[]
        self.active_users:list[str]=[]
        self.participants:list[str]=[]
    
    def define_participants(self,redis,chat_id):
        self.participants=(redis.lrange(chat_id,0,-1) or [])
        
    async def connect(self,websocket:WebSocket,username):
        if username not in self.participants:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="You are not a participant."
            )
        await websocket.accept()
        self.active_users.append(username)
        self.active_connections.append(websocket)
        print(self.active_connections)
        
    def disconnect(self,websocket,username):
        if username in self.active_users:
            self.active_users.remove(username)
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
    async def broadcast(self,message:message_validation,connection,username,chat_id):
        print(message)
        not_active=list(set(self.participants)-set(self.active_users))
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO messages(chat_id,message,sent_by) VALUES(%s,%s,%s) RETURNING message_id',(chat_id,message.get('message'),username))
            message_id=cursor.fetchone().get('message_id',None)
            if message_id is None:
                raise WebSocketException(code=status.WS_1006_ABNORMAL_CLOSURE,reason='DB insertion failed!')
            query='INSERT INTO unread_inbox(username,message_id) VALUES(%s,%s)'
            all_data=[(nac,message_id) for nac in not_active]
            cursor.executemany(query,all_data)
        for connections in self.active_connections:
            await connections.send_json({'chat_id':chat_id,'message':message.get('message'),'username':username})
        connection.commit()