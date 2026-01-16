"""
Mailgun Email Service for sending OTP and other emails
"""

import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MailgunEmailService:
    """
    Service for sending emails via Mailgun API
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'MAILGUN_API_KEY', '')
        self.domain = getattr(settings, 'MAILGUN_DOMAIN', '')
        self.from_email = getattr(settings, 'MAILGUN_FROM_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'))
        self.api_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
    
    def send_email(self, to_email, subject, text_content, html_content=None):
        """
        Send email via Mailgun API
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            text_content (str): Plain text email content
            html_content (str, optional): HTML email content
            
        Returns:
            dict: Response with success status and message
        """
        if not self.api_key or not self.domain:
            logger.error("Mailgun API key or domain not configured")
            return {
                'success': False,
                'error': 'Mailgun not configured'
            }
        
        try:
            data = {
                'from': self.from_email,
                'to': to_email,
                'subject': subject,
                'text': text_content,
            }
            
            # Add HTML content if provided
            if html_content:
                data['html'] = html_content
            
            response = requests.post(
                self.api_url,
                auth=('api', self.api_key),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Mailgun email sent successfully to {to_email}")
                return {
                    'success': True,
                    'message_id': response.json().get('id', ''),
                    'message': 'Email sent successfully'
                }
            else:
                error_msg = f"Mailgun API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Mailgun request failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Mailgun email sending failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
    
    def send_otp_email(self, user, otp_code, purpose='password_reset'):
        """
        Send OTP code via email using Mailgun
        
        Args:
            user: Django User object
            otp_code (str): 6-digit OTP code
            purpose (str): Purpose of OTP (e.g., 'password_reset', 'login')
            
        Returns:
            dict: Response with success status
        """
        if purpose == 'password_reset':
            subject = 'Password Reset OTP - Farm Management System'
            text_content = f"""Hello {user.first_name or user.username},

You have requested to reset your password for the Farm Management System.

Your OTP code is: {otp_code}

This OTP will expire in 10 minutes for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
Farm Management System Team"""
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .otp-box {{ background-color: #fff; border: 2px dashed #4CAF50; padding: 20px; text-align: center; margin: 20px 0; }}
        .otp-code {{ font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name or user.username},</p>
            <p>You have requested to reset your password for the Farm Management System.</p>
            <div class="otp-box">
                <p style="margin-top: 0;">Your OTP code is:</p>
                <div class="otp-code">{otp_code}</div>
            </div>
            <p>This OTP will expire in <strong>10 minutes</strong> for security reasons.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>Farm Management System Team</p>
        </div>
    </div>
</body>
</html>"""
        else:
            # Generic OTP email
            subject = f'Your OTP Code - Farm Management System'
            text_content = f"""Hello {user.first_name or user.username},

Your OTP code is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
Farm Management System Team"""
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .otp-box {{ background-color: #f9f9f9; border: 2px dashed #4CAF50; padding: 20px; text-align: center; margin: 20px 0; }}
        .otp-code {{ font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <p>Hello {user.first_name or user.username},</p>
        <div class="otp-box">
            <p>Your OTP code is:</p>
            <div class="otp-code">{otp_code}</div>
        </div>
        <p>This OTP will expire in 10 minutes.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )

