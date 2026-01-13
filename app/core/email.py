from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from pathlib import Path
from typing import List

# Configuration for fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates' / 'email',
)

fm = FastMail(conf)

async def send_email_async(subject: str, email_to: str, body: dict, template_name: str):
    """
    Generic function to sends an email using a template.
    """
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype="html"
    )
    
    await fm.send_message(message, template_name=template_name)


async def send_verification_email(email_to: str, otp_code: str, name: str):
    """
    Gửi OTP xác thực.
    """
    project_name = settings.PROJECT_NAME
    subject = f"{otp_code} là mã xác nhận của bạn"

    # Body truyền đúng các biến trong file HTML
    await send_email_async(
        subject=subject,
        email_to=email_to,
        body={
            "project_name": project_name,
            "email_to": email_to,
            "name": name,
            "otp_code": otp_code,
        },
        template_name="verification.html"
    )

async def send_password_reset_otp_email(email_to: str, otp_code: str, name: str):
    """
    Gửi OTP để khôi phục mật khẩu.
    """
    project_name = settings.PROJECT_NAME
    subject = f"{otp_code} là mã khôi phục mật khẩu của bạn"

    await send_email_async(
        subject=subject,
        email_to=email_to,
        body={
            "project_name": project_name,
            "email_to": email_to,
            "name": name,
            "otp_code": otp_code,
        },
        template_name="password_reset_otp.html"
    )

async def send_password_reset_email(email_to: str, token: str):
    """
    Formats and sends the password reset email using a template.
    """
    project_name = settings.PROJECT_NAME
    subject = f"Password Reset for {project_name}"
    reset_link = f"{settings.CLIENT_BASE_URL}/reset-password?token={token}"
    
    await send_email_async(
        subject=subject,
        email_to=email_to,
        body={
            "project_name": project_name,
            "email_to": email_to,
            "reset_link": reset_link,
        },
        template_name="password_reset.html"
    )
