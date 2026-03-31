from sqlalchemy import (
    Column, String, Integer, BigInteger, Text,
    ForeignKey, DateTime, func
)
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
    sent_messages = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sent_by"
    )
    user_chats = relationship("UserChat", back_populates="user")
    unread_inbox = relationship("UnreadInbox", back_populates="user")


class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # relationships
    messages = relationship("Message", back_populates="chat")
    user_chats = relationship("UserChat", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    chat_id = Column(
        BigInteger,
        ForeignKey("chats.chat_id", ondelete="CASCADE"),
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
    sender = relationship(
        "User",
        back_populates="sent_messages",
        foreign_keys=[sent_by]
    )


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

    id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=False,
    )
    message_id = Column(
        BigInteger,
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=True
    )

    # relationship
    user = relationship("User", back_populates="unread_inbox")