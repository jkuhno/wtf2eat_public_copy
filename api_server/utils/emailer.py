import os
import aiosmtplib # type: ignore
from email.message import EmailMessage
from fastapi import HTTPException # type: ignore

import ssl
import certifi # type: ignore

ssl_context = ssl.create_default_context(cafile=certifi.where())

# Email Configuration
SMTP_HOST = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT"))
SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASSWORD")



async def send_email(to: str, subject: str, content: str):
    """Securely send an email using an SMTP server"""

    mail_from = 'info@wtf2eat.com'

    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(content)

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
            start_tls=True,  # Secure connection
            tls_context=ssl_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {e}")


