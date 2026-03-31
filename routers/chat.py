from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from connections.connection_db import get_db
from connections.connection_redis import get_redis
from utils.token import JWTTokenClass
from utils.validation_models import add_contact_validation
from connections.schemas import UserChat
from connections.schemas import Message

router = APIRouter(
    prefix='/chat/{chat_id}'
)


@router.get('/participants')
def get_chat_participants(
    chat_id: str,
    redis=Depends(get_redis),
    username: str = Depends(JWTTokenClass.get_user)
):
    try:
        participants = redis.lrange(str(chat_id), 0, -1)
        return JSONResponse(content={'participants': participants})
    except Exception:
        return JSONResponse(
            content={'message': 'You are not a participant in this chat.', 'remarks': 'Permission Denied'},
            status_code=status.HTTP_401_UNAUTHORIZED
        )


@router.post('/participants/add', status_code=status.HTTP_201_CREATED)
def add_participant(
    chat_id: str,
    contact: add_contact_validation,
    username: str = Depends(JWTTokenClass.get_user),
    redis=Depends(get_redis),
    db: Session = Depends(get_db)
):
    participants = redis.lrange(chat_id, 0, -1)

    if username not in participants:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'message': 'Not authorized to add people!'}
        )
    if contact.username in participants:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail={'message': 'User already part of group!!'}
        )

    try:
        new_participant = UserChat(username=contact.username, chat_id=chat_id)
        db.add(new_participant)
        db.commit()
        db.refresh(new_participant)

        redis.lpush(chat_id, contact.username)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={'message': 'Participant Added!'}
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': 'Unable to add participant'}
        )


@router.get('/messages')
def get_messages(
    chat_id: str,
    limit: int = Query(20),
    offset: int = Query(0),
    username: str = Depends(JWTTokenClass.get_user),
    db: Session = Depends(get_db),
    redis=Depends(get_redis)
):
    participants = redis.lrange(chat_id, 0, -1)

    if username not in participants:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'message': 'You are not a participant in this chat.'}
        )

    try:
        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.date_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        all_messages = [
            {
                'message_id': message.message_id,
                'datetime': str(message.date_time),
                'message': message.message,
                'sent_by': message.sent_by
            }
            for message in messages
        ]

        return JSONResponse(content=all_messages, status_code=status.HTTP_200_OK)

    except SQLAlchemyError:
        return JSONResponse(
            content={'error': 'Unable to fetch data'},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )