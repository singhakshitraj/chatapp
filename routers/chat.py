from fastapi import APIRouter,HTTPException,status,Depends
from fastapi.responses import JSONResponse
from db.connection_db import db_connect
from db.connection_redis import get_redis
from utils.token import JWTTokenClass
from psycopg2.errors import ReadingSqlDataNotPermitted
router=APIRouter(
    prefix= '/chat/{chat_id}'
)

@router.get(path='/participants')
def get_chat_participants(chat_id:str,redis=Depends(get_redis),username=Depends(JWTTokenClass.get_user)):
    try:
        participants=redis.lrange(str(chat_id),0,-1)
        """ if username not in participants:
            raise ReadingSqlDataNotPermitted """
        return JSONResponse(content={'participants':participants})
    except ReadingSqlDataNotPermitted as e:
        return JSONResponse({'message':'You are not a participant in this chat.','remarks':'Permission Denied,'},status_code=status.HTTP_401_UNAUTHORIZED)
