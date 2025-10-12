from fastapi_mail import ConnectionConfig,MessageSchema,FastMail
import os
from connections.connection_celery import celery_app
import asyncio

configs = ConnectionConfig(
    MAIL_USERNAME= os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD= os.environ.get('MAIL_PASSWORD'),
    MAIL_FROM= os.environ.get('MAIL_FROM'),
    MAIL_PORT= os.environ.get('MAIL_PORT'),
    MAIL_SERVER= os.environ.get('MAIL_SERVER'),
    MAIL_STARTTLS= os.environ.get('MAIL_STARTTLS'),
    MAIL_SSL_TLS= os.environ.get('MAIL_SSL_TLS'),
    USE_CREDENTIALS= os.environ.get('USE_CREDENTIALS'),
    VALIDATE_CERTS= os.environ.get('VALIDATE_CERTS'),
)

@celery_app.task
def send_email(to:str,subject:str,body:str):
    asyncio.run(email_sender_process(to=to,subject=subject,body=body))

async def email_sender_process(to:str,subject:str,body:str):
    message=MessageSchema(
        recipients=[to],
        subject=subject,
        body=body
    )
    fmail=FastMail(config=configs)
    await fmail.send_message(message=message)