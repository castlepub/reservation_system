import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ZohoEmailService:
    def __init__(self):
        # Allow region override (e.g., smtp.zoho.eu)
        self.smtp_server = os.getenv("ZOHO_SMTP_HOST", "smtp.zoho.com")
        self.smtp_port = int(os.getenv("ZOHO_SMTP_PORT", "587"))
        # Support both ZOHO_EMAIL and ZOHO_MAIL env names
        self.username = os.getenv("ZOHO_EMAIL") or os.getenv("ZOHO_MAIL")
        self.password = os.getenv("ZOHO_PASSWORD") or os.getenv("ZOHO_APP_PASSWORD")
        self.from_email = os.getenv("ZOHO_EMAIL") or os.getenv("ZOHO_MAIL")
        
        if not all([self.username, self.password, self.from_email]):
            logger.warning("Zoho email credentials not configured. Email functionality will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send email via Zoho Mail"""
        if not self.enabled:
            logger.warning("Email service not configured, skipping email send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            if reply_to:
                try:
                    msg['Reply-To'] = reply_to
                except Exception:
                    pass
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_reservation_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        reservation_data: dict
    ) -> bool:
        """Send reservation confirmation email"""
        subject = f"Reservation Confirmed - The Castle Pub"
        
        html_content = f"""
        <html>
        <body>
            <h2>Reservation Confirmed!</h2>
            <p>Dear {customer_name},</p>
            <p>Your reservation at The Castle Pub has been confirmed.</p>
            
            <h3>Reservation Details:</h3>
            <ul>
                <li><strong>Date:</strong> {reservation_data['date']}</li>
                <li><strong>Time:</strong> {reservation_data['time']}</li>
                <li><strong>Duration:</strong> {reservation_data['duration_hours']} hours</li>
                <li><strong>Party Size:</strong> {reservation_data['party_size']} people</li>
                <li><strong>Room:</strong> {reservation_data['room_name']}</li>
            </ul>
            
            <p>If you need to make any changes to your reservation, please contact us.</p>
            
            <p>Thank you for choosing The Castle Pub!</p>
            
            <hr>
            <p><small>This is an automated confirmation email.</small></p>
        </body>
        </html>
        """
        
        text_content = f"""
        Reservation Confirmed!
        
        Dear {customer_name},
        
        Your reservation at The Castle Pub has been confirmed.
        
        Reservation Details:
        - Date: {reservation_data['date']}
        - Time: {reservation_data['time']}
        - Duration: {reservation_data['duration_hours']} hours
        - Party Size: {reservation_data['party_size']} people
        - Room: {reservation_data['room_name']}
        
        If you need to make any changes to your reservation, please contact us.
        
        Thank you for choosing The Castle Pub!
        """
        
        return self.send_email(customer_email, subject, html_content, text_content)
    
    def send_admin_notification(
        self,
        admin_email: str,
        notification_type: str,
        data: dict
    ) -> bool:
        """Send notification email to admin"""
        subject = f"Admin Notification - {notification_type}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Admin Notification</h2>
            <p><strong>Type:</strong> {notification_type}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>Details:</h3>
            <pre>{str(data)}</pre>
        </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, html_content) 