from fastapi import APIRouter,Depends,status,HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from connections.connection_db import db_connect
from utils.passwords import PasswordHelpers
from utils.token import JWTTokenClass
from dotenv import load_dotenv
router=APIRouter(
    prefix='/auth',
    tags=['Auth']
)

@router.post('/login')
def login(data=Depends(OAuth2PasswordRequestForm),connection=Depends(db_connect)):
    with connection.cursor() as cursor:
        load_dotenv()
        cursor.execute(f'SELECT * FROM users WHERE username=%s',(data.username,))
        user=cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail={'message':'User not found!!'})
        if not PasswordHelpers.verify_password(data.password,user.get('password')):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={'message':'Incorrect Credentials!!'})
        token=JWTTokenClass.generate_token(user=user)
        return JSONResponse(content={'username':user.get('username'),'token':token},status_code=status.HTTP_200_OK)
    
@router.post('/register',status_code=status.HTTP_201_CREATED)
def register(data=Depends(OAuth2PasswordRequestForm),connection=Depends(db_connect)):
    with connection.cursor() as cursor:
        load_dotenv()
        cursor.execute('SELECT username FROM users WHERE username=%s',(data.username,))
        user=cursor.fetchone()
        if user is not None:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail={'message':'user already exists with these credentials','suggestion':'try logging in'})
        cursor.execute('INSERT INTO users(username,password) VALUES (%s,%s)',(data.username,PasswordHelpers.hash_password(data.password)))
        connection.commit()
        user={
            'username':data.username,
            'password':data.password
        }
        token=JWTTokenClass.generate_token(user=user)
        return JSONResponse(content={'username':user.get('username'),'token':token},status_code=status.HTTP_201_CREATED)