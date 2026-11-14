from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from auth.auth import create_tokens, decode_token, create_reset_token
from config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: str, host: str):
    token = create_tokens({"sub": email})["access_token"]
    
    html_content = f"""
    <h3>Підтвердження електронної пошти</h3>
    <p>Будь ласка, перейдіть за посиланням нижче для підтвердження вашого акаунта:</p>
    <a href="{host}auth/confirmed_email/{token}">Підтвердити пошту</a>
    """

    message = MessageSchema(
        subject="Підтвердження реєстрації",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_reset_password_email(email: str, host: str):
    token = create_reset_token(email)
    
    html_content = f"""
    <h3>Скидання паролю</h3>
    <p>Для встановлення нового пароля перейдіть за посиланням нижче:</p>
    <a href="{host}auth/reset-password-page/{token}">Встановити новий пароль</a>
    """

    message = MessageSchema(
        subject="Запит на скидання паролю",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)