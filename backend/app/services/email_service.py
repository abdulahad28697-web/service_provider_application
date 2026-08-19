"""Service for sending transactional emails (password reset, notifications)."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Handles transactional email dispatches."""

    def __init__(self) -> None:
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        self.frontend_url = settings.FRONTEND_URL.rstrip("/")

    def send_password_reset_email(
        self,
        to_email: str,
        full_name: str,
        reset_token: str,
    ) -> bool:
        """
        Send a secure password reset email with a verification link.
        """
        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"
        subject = "Reset Your ServiceHub Password"

        text_content = f"""Hello {full_name or 'User'},

You recently requested to reset your password for your ServiceHub AI account.

Click or open the link below to approve and reset your password:
{reset_link}

This link is valid for 1 hour. If you did not request a password reset, please ignore this email.

Best regards,
The ServiceHub Team
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .header {{ text-align: center; margin-bottom: 24px; }}
    .brand {{ font-size: 24px; font-weight: 700; color: #0284c7; }}
    .content {{ font-size: 15px; line-height: 1.6; color: #334155; }}
    .button-container {{ text-align: center; margin: 30px 0; }}
    .button {{ display: inline-block; background-color: #0284c7; color: #ffffff !important; font-weight: 600; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-size: 15px; }}
    .footer {{ font-size: 13px; color: #64748b; margin-top: 28px; border-top: 1px solid #e2e8f0; padding-top: 16px; }}
    .token-ref {{ word-break: break-all; color: #0284c7; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="brand">ServiceHub AI</div>
    </div>
    <div class="content">
      <p>Hello <strong>{full_name or 'there'}</strong>,</p>
      <p>We received a request to reset the password for your ServiceHub account.</p>
      <p>Click the button below to approve and set your new password:</p>
      <div class="button-container">
        <a href="{reset_link}" class="button" target="_blank">Reset Password</a>
      </div>
      <p>Or copy and paste this verification URL into your browser:</p>
      <p class="token-ref"><a href="{reset_link}">{reset_link}</a></p>
      <p>This link will expire in <strong>1 hour</strong>. If you did not request a password reset, you can safely ignore this email.</p>
    </div>
    <div class="footer">
      <p>&copy; ServiceHub AI Platform. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

        print(
            "\n======================================================\n"
            "[EMAIL SERVICE] Password Reset Email Dispatched\n"
            f"To: {to_email}\n"
            f"Subject: {subject}\n"
            f"Reset Link: {reset_link}\n"
            "======================================================\n",
            flush=True,
        )

        if not self.smtp_host or not self.smtp_user:
            logger.info("SMTP_HOST or SMTP_USER not configured. Password reset link printed to console above.")
            return True

        try:
            from_addr = self.from_email or self.smtp_user
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{from_addr}>"
            msg["To"] = to_email

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            if int(self.smtp_port) == 465:
                with smtplib.SMTP_SSL(self.smtp_host, int(self.smtp_port), timeout=15) as server:
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(from_addr, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_host, int(self.smtp_port), timeout=15) as server:
                    if self.smtp_tls:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(from_addr, [to_email], msg.as_string())

            logger.info(
                "Password reset email successfully dispatched to %s via SMTP (%s:%s)",
                to_email,
                self.smtp_host,
                self.smtp_port,
            )
            return True
        except Exception as exc:
            logger.error(
                "Failed to transmit email to %s via SMTP (%s:%s): %s",
                to_email,
                self.smtp_host,
                self.smtp_port,
                exc,
            )
            print(f"[EMAIL SERVICE ERROR] Failed to send email to {to_email}: {exc}", flush=True)
            return False
