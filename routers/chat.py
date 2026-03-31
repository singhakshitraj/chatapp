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
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
    username=Depends(JWTTokenClass.get_user)
):
    # Try Redis first
    participants = redis.lrange(str(chat_id), 0, -1) or []

    # On cache miss, load from DB and repopulate Redis
    if not participants:
        rows = (
            db.query(UserChat.username)
            .filter(UserChat.chat_id == chat_id)
            .all()
        )
        participants = [row.username for row in rows]

        if participants:
            redis.lpush(chat_id, *participants)

    return JSONResponse(content={'participants': participants})


@router.post('/participants/add')
def add_participant(
    chat_id: str,
    contact: add_contact_validation,
    db: Session = Depends(get_db),
    username=Depends(JWTTokenClass.get_user),
    redis=Depends(get_redis),
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
        db.add(UserChat(username=contact.username, chat_id=chat_id))
        db.commit()
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
    limit=Query(20),
    offset=Query(0),
    username=Depends(JWTTokenClass.get_user),
    db: Session = Depends(get_db),
    redis=Depends(get_redis)
):
    participants = redis.lrange(chat_id, 0, -1) or []
    # On cache miss, load from DB and repopulate Redis
    if not participants:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT username FROM user_chats WHERE chat_id = %s',
                (chat_id,)
            )
            rows = cursor.fetchall()
            participants = [row.get('username') for row in rows]

        if participants:
            redis.lpush(chat_id, *participants)
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
                'message_id': str(message.message_id),
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
