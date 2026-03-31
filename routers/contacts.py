from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from connections.connection_db import get_db
from connections.connection_redis import get_redis
from utils.token import JWTTokenClass
from utils.validation_models import add_contact_validation
from connections.schemas import User
from connections.schemas import UserChat
from connections.schemas import Chat

router = APIRouter(
    prefix='/contacts'
)


@router.get('/', status_code=status.HTTP_200_OK)
def contact_list(
    db: Session = Depends(get_db),
    username: str = Depends(JWTTokenClass.get_user)
):
    try:
        contacts = (
            db.query(UserChat.chat_id)
            .filter(UserChat.username == username)
            .all()
        )
        return {'contacts': [c.chat_id for c in contacts]}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail={'message': 'DB error has occurred!', 'error': str(e)}
        )


@router.post('/add')
def add_to_contact(
    contact: add_contact_validation,
    db: Session = Depends(get_db),
    username: str = Depends(JWTTokenClass.get_user),
    redis=Depends(get_redis)
):
    # Check receiver exists
    receiver = db.query(User).filter(User.username == contact.username).first()
    if receiver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'message': 'No user with particular username exists.'}
        )

    # Self-contact guard
    if username == contact.username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'message': 'Loop Detected!!'}
        )

    # Check if a shared chat already exists between the two users
    existing = (
        db.query(UserChat.chat_id)
        .filter(UserChat.username == username)
        .intersect(
            db.query(UserChat.chat_id)
            .filter(UserChat.username == contact.username)
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'message': 'Contact already exists', 'error': 'Unique Constraint Violation'}
        )

    try:
        # Create a new chat
        new_chat = Chat()
        db.add(new_chat)
        db.flush()  # flush to get the generated chat_id without committing yet

        # Add both participants
        db.add_all([
            UserChat(username=username, chat_id=new_chat.chat_id),
            UserChat(username=contact.username, chat_id=new_chat.chat_id)
        ])

        db.commit()

        # Push both participants into Redis
        redis.lpush(new_chat.chat_id, username)
        redis.lpush(new_chat.chat_id, contact.username)

        return {
            'message': 'Success!',
            'contact': {
                'party1': username,
                'party2': contact.username
            }
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'message': 'Contact already exists', 'error': 'Unique Constraint Violation'}
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'message': str(e)}
        )