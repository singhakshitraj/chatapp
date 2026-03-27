from fastapi import APIRouter,HTTPException,status,Depends,Query
from fastapi.responses import JSONResponse
from connections.connection_db import db_connect
from connections.connection_redis import get_redis
from utils.token import JWTTokenClass
from psycopg2.errors import ReadingSqlDataNotPermitted,DatabaseError
from utils.validation_models import add_contact_validation
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

@router.post('/participants/add')
def add_participant(chat_id:str,contact:add_contact_validation,username=Depends(JWTTokenClass.get_user),redis=Depends(get_redis),connection=Depends(db_connect)):
    participants=redis.lrange(chat_id,0,-1)
    if username not in participants:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={'message':'Not authorized to add people!'})
    if contact.username in participants:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail={'message':'User already part of group!!'})
    with connection.cursor() as cursor:
        try:
            cursor.execute('INSERT INTO user_chats(username,chat_id) VALUES(%s,%s) RETURNING *',(contact.username,chat_id))
            result=cursor.fetchone()
            if result is None:
                raise DatabaseError
            redis.lpush(chat_id,contact.username)
            return JSONResponse(status_code=status.HTTP_201_CREATED,content={'message':'Participant Added!'})
        except DatabaseError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={'message':'Unable to add participant'})

@router.get('/messages')
def get_messages(chat_id:str,limit=Query(20),offset=Query(0),username=Depends(JWTTokenClass.get_user),connection=Depends(db_connect),redis=Depends(get_redis)):
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
            all_messages=[{
                'message_id':message.get('message_id'),
                'datetime':str(message.get('date_time')),
                'message':message.get('message'),
                'sent_by':message.get('sent_by')
            } for message in messages]
            return JSONResponse(
                content=all_messages,
                status_code=status.HTTP_200_OK)
        except DatabaseError as e:
            return JSONResponse(content={'error':'Unable to fetch data'},status_code=status.HTTP_503_SERVICE_UNAVAILABLE)