from fastapi import APIRouter,HTTPException,status,Depends,Query
from fastapi.responses import JSONResponse
from db.connection_db import db_connect
from db.connection_redis import get_redis
from utils.token import JWTTokenClass
from psycopg2.errors import ReadingSqlDataNotPermitted,DatabaseError
router=APIRouter(
    prefix= '/chat/{chat_id}'
)

@router.get('/participants')
def get_chat_participants(chat_id:str,redis=Depends(get_redis),username=Depends(JWTTokenClass.get_user)):
    try:
        participants=redis.lrange(str(chat_id),0,-1)
        """ if username not in participants:
            raise ReadingSqlDataNotPermitted """
        return JSONResponse(content={'participants':participants})
    except ReadingSqlDataNotPermitted as e:
        return JSONResponse({'message':'You are not a participant in this chat.','remarks':'Permission Denied,'},status_code=status.HTTP_401_UNAUTHORIZED)

@router.get('/messages')
def get_messages(chat_id:str,limit=Query(20),offset=Query(20),username=Depends(JWTTokenClass.get_user),connection=Depends(db_connect),redis=Depends(get_redis)):
    participants=redis.lrange(chat_id,0,-1)
    if username not in participants:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={'message':'You are not a participant in this chat.'})
    with connection.cursor() as cursor:
        try:
            cursor.execute('''
            SELECT message_id,date_time,message,sent_by FROM messages 
            WHERE chat_id=%s 
            ORDER BY date_time DESC
            LIMIT %s OFFSET %s
            ''',(chat_id,limit,offset)
            )
            messages=cursor.fetchall()
            return JSONResponse(content={'data':messages},status_code=status.HTTP_200_OK)
        except DatabaseError as e:
            return JSONResponse(content={'error':'Unable to fetch data'},status_code=status.HTTP_503_SERVICE_UNAVAILABLE)