import uuid
from sqlalchemy import (
    Column, String, Integer, BigInteger, Text,
    ForeignKey, DateTime, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    username = Column(String(64), primary_key=True, index=True)
    password = Column(String(256), nullable=True)
    email    = Column(String(256), default="akshit.22209@knit.ac.in")

    # relationships
    sent_messages = relationship("Message",  back_populates="sender",     foreign_keys="Message.sent_by")
    user_chats    = relationship("UserChat", back_populates="user")
    unread_inbox  = relationship("UnreadInbox", back_populates="user")


class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # relationships
    messages   = relationship("Message",  back_populates="chat")
    user_chats = relationship("UserChat", back_populates="chat")


class Message(Base):
    """
    Parent (partitioned) table.
    SQLAlchemy manages the parent table definition; the four hash-partition
    child tables are created via raw DDL in the Alembic migration so that
    Postgres can route rows automatically.
    """
    __tablename__ = "messages"
    __table_args__ = {
        "postgresql_partition_by": "HASH (chat_id)",
    }

    message_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        nullable=False
    )
    chat_id   = Column(
        BigInteger,
        ForeignKey("chats.chat_id", ondelete="CASCADE"),
        primary_key=True,          # composite PK with message_id
        nullable=False,
    )
    date_time = Column(DateTime, server_default=func.now())
    message   = Column(String(512), nullable=True)
    sent_by   = Column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=True,
    )

    # relationships
    chat   = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sent_by])


class UserChat(Base):
    __tablename__ = "user_chats"

    username = Column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        primary_key=True,
    )
    chat_id = Column(
        BigInteger,
        ForeignKey("chats.chat_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # relationships
    user = relationship("User", back_populates="user_chats")
    chat = relationship("Chat", back_populates="user_chats")


class UnreadInbox(Base):
    __tablename__ = "unread_inbox"

    # No single-column PK in original DDL; we add a surrogate for ORM usability.
    # The real uniqueness constraint is (username, message_id).
    id = Column(Integer, primary_key=True, autoincrement=True)

    username   = Column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=False,
    )
    message_id = Column(UUID(as_uuid=True), nullable=True)

    # relationship
    user = relationship("User", back_populates="unread_inbox")