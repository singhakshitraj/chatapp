from fastapi_mail import ConnectionConfig,MessageSchema,FastMail
import os
from celery_worker import celery_app
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
def send_email(to:str,subject:str):
    asyncio.run(email_sender_process(to=to,subject=subject))

async def email_sender_process(to:str,subject:str):
    body='''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Rate Limit Notification</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <p>Hello,</p>

  <p>
    This is to inform you that your recent activity has exceeded the allowed usage rate. 
    As a result, throttling has been temporarily applied to maintain system stability 
    and fair access for all users. Access will be restored automatically once normal 
    usage levels resume.
  </p>

  <p>
    We recommend reviewing your usage patterns and implementing rate management to avoid 
    future interruptions.
  </p>

  <p>Thank you for your understanding,</p>

  <p>
    The Support Team<br>
    ChatApp → singhakshitraj
  </p>
</body>
</html>
    '''
    message=MessageSchema(
        recipients=[to],
        subject=subject,
        body=body,
        subtype="html"
    )
    fmail=FastMail(config=configs)
    await fmail.send_message(message=message)