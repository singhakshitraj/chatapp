from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from connections.connection_db import get_db
from connections.schemas import User
from utils.passwords import PasswordHelpers
from utils.token import JWTTokenClass

router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)

@router.post('/login')
def login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'message': 'User not found!!'}
        )
    if not PasswordHelpers.verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'message': 'Incorrect Credentials!!'}
        )

    token = JWTTokenClass.generate_token(user={'username': user.username, 'password': user.password})
    return JSONResponse(
        content={'username': user.username, 'access_token': token,'token_type':'bearer'},
        status_code=status.HTTP_200_OK
    )


@router.post('/register', status_code=status.HTTP_201_CREATED)
def register(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == data.username).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail={'message': 'User already exists with this username', 'suggestion': 'Try logging in'}
        )

    new_user = User(
        username=data.username,
        password=PasswordHelpers.hash_password(data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = JWTTokenClass.generate_token(user={'username': new_user.username, 'password': data.password})
    return JSONResponse(
        content={'username': new_user.username,'access_token': token,'token_type':'bearer'},
        status_code=status.HTTP_201_CREATED
    )