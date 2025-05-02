import os
import smtplib
import time
import logging
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate
from datetime import datetime
from flask import current_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email service class remains unchanged
class EmailService:
    """Enhanced email service with retry capability and better error handling"""
    
    def __init__(self, app=None):
        """Initialize the email service with Flask app or environment variables"""
        self.app = app
        
        # Default SMTP settings
        self.smtp_server = None
        self.smtp_port = None
        self.username = None
        self.password = None
        self.use_tls = True
        self.use_ssl = False
        self.default_sender = None
        self.sender_name = None
        
        # Max retries for sending emails
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        if app:
            self.init_app(app)
        else:
            self._load_config_from_env()
    
    def init_app(self, app):
        """Initialize with Flask application"""
        self.app = app
        self._load_config_from_app()
    
    def _load_config_from_env(self):
        """Load configuration from environment variables"""
        self.smtp_server = os.getenv('MAIL_SERVER')
        self.smtp_port = int(os.getenv('MAIL_PORT', '587'))
        self.username = os.getenv('MAIL_USERNAME')
        self.password = os.getenv('MAIL_PASSWORD')
        self.use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
        self.use_ssl = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
        self.default_sender = os.getenv('MAIL_DEFAULT_SENDER')
        self.sender_name = os.getenv('MAIL_SENDER_NAME', 'JetCam Studio')
        
        # Load retry configuration
        self.max_retries = int(os.getenv('MAIL_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('MAIL_RETRY_DELAY', '2'))
    
    def _load_config_from_app(self):
        """Load configuration from Flask application"""
        if not self.app:
            return
            
        self.smtp_server = self.app.config.get('MAIL_SERVER')
        self.smtp_port = int(self.app.config.get('MAIL_PORT', 587))
        self.username = self.app.config.get('MAIL_USERNAME')
        self.password = self.app.config.get('MAIL_PASSWORD')
        self.use_tls = self.app.config.get('MAIL_USE_TLS', True)
        self.use_ssl = self.app.config.get('MAIL_USE_SSL', False)
        self.default_sender = self.app.config.get('MAIL_DEFAULT_SENDER')
        self.sender_name = self.app.config.get('MAIL_SENDER_NAME', 'JetCam Studio')
        
        # Load retry configuration
        self.max_retries = int(self.app.config.get('MAIL_MAX_RETRIES', 3))
        self.retry_delay = int(self.app.config.get('MAIL_RETRY_DELAY', 2))
    
    def validate_config(self):
        """Validate that required configuration is present"""
        missing = []
        
        if not self.smtp_server:
            missing.append('MAIL_SERVER')
        if not self.smtp_port:
            missing.append('MAIL_PORT')
        if not self.username:
            missing.append('MAIL_USERNAME')
        if not self.password:
            missing.append('MAIL_PASSWORD')
        if not self.default_sender:
            missing.append('MAIL_DEFAULT_SENDER')
        
        if missing:
            raise ValueError(f"Missing required email configuration: {', '.join(missing)}")
        
        return True
    
    def send_email(self, to_email, subject, html_content, from_email=None, sender_name=None, retry=True):
        """
        Send an email with HTML content to a recipient
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_content (str): HTML content of the email
            from_email (str, optional): Sender email address
            sender_name (str, optional): Name to display as sender
            retry (bool): Whether to retry sending on failure
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            ValueError: If configuration is missing
            RuntimeError: If email sending fails after retries
        """
        # Validate configuration
        self.validate_config()
        
        # Get sender email and name
        sender_email = from_email or self.default_sender
        display_name = sender_name or self.sender_name
        
        # Format sender with name if provided
        if display_name:
            formatted_sender = formataddr((display_name, sender_email))
        else:
            formatted_sender = sender_email
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = formatted_sender
        message['To'] = to_email
        message['Date'] = formatdate(localtime=True)
        message['Message-ID'] = f"<{int(time.time())}@{sender_email.split('@')[1]}>"
        
        # Add Reply-To header if different from sender
        if from_email and from_email != self.default_sender:
            message['Reply-To'] = from_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Add plain text alternative (basic version of the HTML)
        # This helps with spam filters and readability in text-only clients
        plain_text = self._html_to_plain_text(html_content)
        text_part = MIMEText(plain_text, 'plain')
        message.attach(text_part)
        
        # Add some headers to reduce spam classification
        message['X-Mailer'] = 'JetCam Studio App'
        
        # Attempt to send email with retries if enabled
        attempts = 0
        max_attempts = self.max_retries if retry else 1
        
        while attempts < max_attempts:
            attempts += 1
            try:
                return self._send(message, sender_email, to_email)
            except Exception as e:
                logger.error(f"Email sending attempt {attempts} failed: {str(e)}")
                
                if attempts < max_attempts:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    error_msg = f"Failed to send email after {max_attempts} attempts: {str(e)}"
                    logger.error(error_msg)
                    if self.app:
                        current_app.logger.error(error_msg)
                    raise RuntimeError(error_msg)
    
    def _send(self, message, sender_email, to_email):
        """Internal method to send the email via SMTP"""
        # Choose appropriate SMTP class based on SSL setting
        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        
        # Connect to SMTP server
        server = smtp_class(self.smtp_server, self.smtp_port)
        
        try:
            # Start TLS if needed
            if self.use_tls and not self.use_ssl:
                server.starttls()
            
            # Login
            server.login(self.username, self.password)
            
            # Send email
            server.sendmail(sender_email, to_email, message.as_string())
            
            log_msg = f"Email sent to {to_email}: {message['Subject']}"
            logger.info(log_msg)
            if self.app:
                current_app.logger.info(log_msg)
                
            return True
        finally:
            # Always close the connection
            server.quit()
    
    def _html_to_plain_text(self, html):
        """Convert HTML to plain text (basic implementation)"""
        text = html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        text = text.replace('<p>', '\n').replace('</p>', '\n')
        text = text.replace('<div>', '\n').replace('</div>', '\n')
        text = text.replace('<h1>', '\n\n').replace('</h1>', '\n')
        text = text.replace('<h2>', '\n\n').replace('</h2>', '\n')
        text = text.replace('<h3>', '\n\n').replace('</h3>', '\n')
        text = text.replace('<li>', '\n- ').replace('</li>', '')
        
        # Remove all other HTML tags
        import re
        text = re.sub(r'<[^>]*>', '', text)
        
        # Replace multiple newlines with just two
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

# OPTIMIZED EMAIL TEMPLATES

def send_welcome_email(user_email, username):
    """Send welcome email to newly registered user"""
    email_service = EmailService()
    current_year = datetime.now().year
    subject = "Welcome to JetCam Studio"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="x-apple-disable-message-reformatting">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>Welcome to JetCam Studio</title>
        <style>
            @media only screen and (max-width: 600px) {{
                .container {{ width: 100% !important; padding: 16px !important; }}
                .button {{ width: 100% !important; }}
                .header img {{ max-width: 120px !important; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f5f5f5; color: #333333;">
        <table role="presentation" width="100%" style="background-color: #f5f5f5;" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center">
                    <table role="presentation" class="container" width="600" style="margin: 24px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden;" cellpadding="0" cellspacing="0">
                        <!-- Header -->
                        <tr>
                            <td class="header" style="background-color: #1a73e8; padding: 24px; text-align: center;">
                                <img src="https://jetcamstudio.com/wp-content/uploads/2023/04/Untitled-9-1-2.png" alt="JetCam Studio Logo" style="max-width: 150px; height: auto; border: 0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 32px;">
                                <h1 style="margin: 0 0 16px; font-size: 24px; font-weight: 600; color: #202124;">Welcome, {username}!</h1>
                                <p style="margin: 0 0 24px; font-size: 16px; line-height: 24px;">Your JetCam Studio account is ready. Start monitoring your streams by accessing your dashboard.</p>
                                <!-- CTA Button -->
                                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <a href="http://live-stream-monitoring-vue3-flask.vercel.app/login" class="button" style="display: inline-block; padding: 12px 24px; background-color: #1a73e8; color: #ffffff; text-decoration: none; border-radius: 4px; font-size: 16px; font-weight: 500; min-width: 180px; text-align: center;">Go to Dashboard</a>
                                        </td>
                                    </tr>
                                </table>
                                <!-- Features -->
                                <table role="presentation" style="margin: 24px 0; width: 100%;" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding: 8px 0; font-size: 16px;">
                                            <strong style="color: #1a73e8;">🔍 Stream Monitoring:</strong> Detect policy violations to keep your channel safe.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-size: 16px;">
                                            <strong style="color: #1a73e8;">💬 Chat Analysis:</strong> Filter inappropriate content in real-time.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-size: 16px;">
                                            <strong style="color: #1a73e8;">🚨 Instant Alerts:</strong> Stay informed with immediate notifications.
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 24px 0 0; font-size: 14px;">Need help? Contact us at <a href="mailto:support@jetcamstudio.com" style="color: #1a73e8; text-decoration: none;">support@jetcamstudio.com</a>.</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 16px; background-color: #f5f5f5; text-align: center; font-size: 12px; color: #666666;">
                                <p style="margin: 0;">© {current_year} JetCam Studio. All rights reserved.</p>
                                <p style="margin: 4px 0 0;">This is an automated message. Please do not reply.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return email_service.send_email(user_email, subject, html_content)

def generate_six_digit_token():
    """Generate a secure 6-digit token"""
    return str(random.randint(100000, 999999))

def send_password_reset_email(user_email, token):
    """Send password reset email with 6-digit token"""
    email_service = EmailService()
    current_year = datetime.now().year
    subject = "JetCam Studio Password Reset Code"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="x-apple-disable-message-reformatting">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>Password Reset Code</title>
        <style>
            @media only screen and (max-width: 600px) {{
                .container {{ width: 100% !important; padding: 16px !important; }}
                .button {{ width: 100% !important; }}
                .code-box {{ font-size: 24px !important; letter-spacing: 3px !important; }}
                .header img {{ max-width: 120px !important; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f5f5f5; color: #333333;">
        <table role="presentation" width="100%" style="background-color: #f5f5f5;" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center">
                    <table role="presentation" class="container" width="600" style="margin: 24px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden;" cellpadding="0" cellspacing="0">
                        <!-- Header -->
                        <tr>
                            <td class="header" style="background-color: #d32f2f; padding: 24px; text-align: center;">
                                <img src="https://jetcamstudio.com/wp-content/uploads/2023/04/Untitled-9-1-2.png" alt="JetCam Studio Logo" style="max-width: 150px; height: auto; border: 0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 32px;">
                                <h1 style="margin: 0 0 16px; font-size: 24px; font-weight: 600; color: #202124;">Password Reset Code</h1>
                                <p style="margin: 0 0 24px; font-size: 16px; line-height: 24px;">Use the code below to reset your JetCam Studio account password. This code expires in 1 hour.</p>
                                <!-- Code Box -->
                                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 16px; background-color: #f1f3f4; border-radius: 4px;">
                                            <div class="code-box" style="font-size: 32px; font-weight: bold; letter-spacing: 5px; font-family: 'Courier New', monospace; color: #202124;">{token}</div>
                                        </td>
                                    </tr>
                                </table>
                                <!-- CTA Button -->
                                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
                                    <tr>
                                        <td align="center">
                                            <a href="http://live-stream-monitoring-vue3-flask.vercel.app/reset-password" class="button" style="display: inline-block; padding: 12px 24px; background-color: #d32f2f; color: #ffffff; text-decoration: none; border-radius: 4px; font-size: 16px; font-weight: 500; min-width: 180px; text-align: center;">Reset Password</a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 24px 0 0; font-size: 14px;">If you didn’t request this, please ignore this email or contact <a href="mailto:support@jetcamstudio.com" style="color: #d32f2f; text-decoration: none;">support@jetcamstudio.com</a>.</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 16px; background-color: #f5f5f5; text-align: center; font-size: 12px; color: #666666;">
                                <p style="margin: 0;">© {current_year} JetCam Studio. All rights reserved.</p>
                                <p style="margin: 4px 0 0;">This is an automated message. Please do not reply.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return email_service.send_email(user_email, subject, html_content)

# Create an instance for direct import
email_service = EmailService()