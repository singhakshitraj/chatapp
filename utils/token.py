from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime,timedelta
import os
from dotenv import load_dotenv
from fastapi import Depends,status
from fastapi.exceptions import HTTPException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

class JWTTokenClass:
    @staticmethod
    def generate_token(user):
        data = {
            'username':user.get('username'),
            'expires_at': str(datetime.now()+timedelta(minutes=int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES'))))
        }
        token=jwt.encode(
            payload=data,
            key=os.environ.get('SECRET_KEY'),
            algorithm=os.environ.get('ALGORITHM')
        )
        return token
    
    @staticmethod
    def get_user(token=Depends(oauth2_scheme)):
        data=jwt.decode(
            jwt=token,
            algorithms=[os.environ.get('ALGORITHM')],
            key=os.environ.get('SECRET_KEY')
        )
        username=data.get('username',{})
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Check JWT Token!!')
        return username