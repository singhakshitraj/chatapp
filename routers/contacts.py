from fastapi import APIRouter,HTTPException,status,Depends
from db.connection_db import db_connect
from utils.token import JWTTokenClass
from utils.validation_models import add_contact_validation
import psycopg2
from dotenv import load_dotenv
router=APIRouter(
    prefix='/contacts'
)

@router.get('/',status_code=status.HTTP_200_OK)
def contact_list(connection=Depends(db_connect),username=Depends(JWTTokenClass.get_user)):
    with connection.cursor() as cursor:
        load_dotenv()
        try:
            cursor.execute('SELECT * FROM user_chats WHERE username=%s',(username,))
            contacts=cursor.fetchall()
            return {'contacts':contacts}
        except BaseException as e:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail={'message':'DB error has occured!'})
    
@router.post('/add')
def add_to_contact(contact:add_contact_validation,connection=Depends(db_connect),username=Depends(JWTTokenClass.get_user)):
    with connection.cursor() as cursor:
        try:
            load_dotenv()
            cursor.execute('SELECT username FROM users WHERE username=%s',(contact.username,))
            reciever=cursor.fetchone()
            if reciever is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail={'message':'No user with particular username exists.'})
            cursor.execute('INSERT INTO chats DEFAULT VALUES RETURNING chat_id')
            chat_id=cursor.fetchone().get('chat_id')
            print(chat_id)
            cursor.execute('''
                INSERT INTO user_chats(username,chat_id)
                VALUES(%s,%s),(%s,%s)            
            ''',(username,chat_id,contact.username,chat_id))
            # STORING CHAT PARTICIPANTS IN REDIS
            connection.commit()
            return {
                'message':'Success!',
                'contact':{
                    'party1':username,
                    'party2':contact.username
                }
            }
        except Exception as e:
            if connection:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail={'message':str(e)})
        