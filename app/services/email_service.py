from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from app.core.config import settings
from app.core.security import create_reservation_token
from app.schemas.reservation import ReservationWithTables
import logging
import os

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.sendgrid_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY) if settings.SENDGRID_API_KEY else None
        # Zoho envs (optional)
        self.zoho_email = os.getenv("ZOHO_EMAIL")
        self.zoho_password = os.getenv("ZOHO_PASSWORD")

    def _try_send_via_zoho(self, to_email: str, subject: str, html_content: str) -> bool:
        try:
            from app.services.email_service_zoho import ZohoEmailService
            zoho = ZohoEmailService()
            if not getattr(zoho, 'enabled', False):
                return False
            return zoho.send_email(to_email, subject, html_content)
        except Exception as e:
            logger.warning(f"Zoho send failed, falling back to SendGrid: {e}")
            return False

    def _send_via_sendgrid(self, to_email: str, customer_name: str, subject: str, html_content: str) -> bool:
        if not self.sendgrid_client:
            logger.warning("SendGrid API key not configured")
            return False
        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, "The Castle Pub"),
            to_emails=To(to_email, customer_name),
            subject=subject,
            html_content=HtmlContent(html_content)
        )
        response = self.sendgrid_client.send(message)
        return response.status_code in [200, 201, 202]

    def send_reservation_confirmation(self, reservation: ReservationWithTables) -> bool:
        """Send confirmation email for a new reservation (Zoho preferred, fallback to SendGrid)."""
        if not reservation.email:
            logger.info("Reservation has no email; skipping confirmation email.")
            return False

        try:
            # Create tokens for cancel/edit links
            cancel_token = create_reservation_token(reservation.id)
            edit_token = create_reservation_token(reservation.id)

            # Build table information
            table_info = ""
            if reservation.tables:
                table_names = [f"{table.table_name} ({table.capacity})" for table in reservation.tables]
                table_info = f"Tables: {', '.join(table_names)}"
            else:
                table_info = "Table assignment pending"

            subject = f"Reservation Confirmation - The Castle Pub"
            
            html_content = f"""
            <html>
            <body>
                <h2>Reservation Confirmation</h2>
                <p>Dear {reservation.customer_name},</p>
                
                <p>Your reservation has been confirmed at <strong>The Castle Pub</strong>.</p>
                
                <h3>Reservation Details:</h3>
                <ul>
                    <li><strong>Date:</strong> {reservation.date.strftime('%A, %B %d, %Y')}</li>
                    <li><strong>Time:</strong> {reservation.time.strftime('%I:%M %p')}</li>
                    <li><strong>Party Size:</strong> {reservation.party_size} people</li>
                    <li><strong>Room:</strong> {reservation.room_name}</li>
                    <li><strong>Tables:</strong> {table_info}</li>
                </ul>
                
                {f'<p><strong>Special Notes:</strong> {reservation.notes}</p>' if reservation.notes else ''}
                
                <h3>Manage Your Reservation:</h3>
                <p>
                    <a href="{settings.FRONTEND_URL}/cancel/{cancel_token}" 
                       style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                        Cancel Reservation
                    </a>
                    <a href="{settings.FRONTEND_URL}/edit/{edit_token}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Modify Reservation
                    </a>
                </p>
                
                <p><strong>Important:</strong> Please arrive 5 minutes before your reservation time.</p>
                
                <p>If you have any questions, please contact us at info@thecastle.de</p>
                
                <p>Thank you for choosing The Castle Pub!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This email was sent to {reservation.email}. 
                    If you did not make this reservation, please contact us immediately.
                </p>
            </body>
            </html>
            """

            # Try Zoho first, then SendGrid
            if self._try_send_via_zoho(reservation.email, subject, html_content):
                logger.info(f"Confirmation email sent via Zoho to {reservation.email}")
                return True
            ok = self._send_via_sendgrid(reservation.email, reservation.customer_name, subject, html_content)
            if ok:
                logger.info(f"Confirmation email sent via SendGrid to {reservation.email}")
            else:
                logger.error("Confirmation email failed via both Zoho and SendGrid")
            return ok
        except Exception as e:
            logger.error(f"Error sending confirmation email: {str(e)}")
            return False

    def send_reservation_update(self, reservation: ReservationWithTables, changes: str) -> bool:
        """Send update notification email"""
        if not self.sendgrid_client:
            logger.warning("SendGrid API key not configured, skipping email")
            return False

        try:
            subject = f"Reservation Updated - The Castle Pub"
            
            html_content = f"""
            <html>
            <body>
                <h2>Reservation Updated</h2>
                <p>Dear {reservation.customer_name},</p>
                
                <p>Your reservation at <strong>The Castle Pub</strong> has been updated.</p>
                
                <h3>Updated Reservation Details:</h3>
                <ul>
                    <li><strong>Date:</strong> {reservation.date.strftime('%A, %B %d, %Y')}</li>
                    <li><strong>Time:</strong> {reservation.time.strftime('%I:%M %p')}</li>
                    <li><strong>Party Size:</strong> {reservation.party_size} people</li>
                    <li><strong>Room:</strong> {reservation.room_name}</li>
                </ul>
                
                <p><strong>Changes Made:</strong> {changes}</p>
                
                <p>If you have any questions, please contact us at info@thecastle.de</p>
                
                <p>Thank you for choosing The Castle Pub!</p>
            </body>
            </html>
            """

            message = Mail(
                from_email=Email(settings.SENDGRID_FROM_EMAIL, "The Castle Pub"),
                to_emails=To(reservation.email, reservation.customer_name),
                subject=subject,
                html_content=HtmlContent(html_content)
            )

            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Update email sent successfully to {reservation.email}")
                return True
            else:
                logger.error(f"Failed to send update email: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"Error sending update email: {str(e)}")
            return False

    def send_reservation_cancellation(self, reservation: ReservationWithTables) -> bool:
        """Send cancellation confirmation email"""
        if not self.sendgrid_client:
            logger.warning("SendGrid API key not configured, skipping email")
            return False

        try:
            subject = f"Reservation Cancelled - The Castle Pub"
            
            html_content = f"""
            <html>
            <body>
                <h2>Reservation Cancelled</h2>
                <p>Dear {reservation.customer_name},</p>
                
                <p>Your reservation at <strong>The Castle Pub</strong> has been cancelled.</p>
                
                <h3>Cancelled Reservation Details:</h3>
                <ul>
                    <li><strong>Date:</strong> {reservation.date.strftime('%A, %B %d, %Y')}</li>
                    <li><strong>Time:</strong> {reservation.time.strftime('%I:%M %p')}</li>
                    <li><strong>Party Size:</strong> {reservation.party_size} people</li>
                    <li><strong>Room:</strong> {reservation.room_name}</li>
                </ul>
                
                <p>We hope to see you again soon!</p>
                
                <p>If you have any questions, please contact us at info@thecastle.de</p>
                
                <p>Thank you for choosing The Castle Pub!</p>
            </body>
            </html>
            """

            message = Mail(
                from_email=Email(settings.SENDGRID_FROM_EMAIL, "The Castle Pub"),
                to_emails=To(reservation.email, reservation.customer_name),
                subject=subject,
                html_content=HtmlContent(html_content)
            )

            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Cancellation email sent successfully to {reservation.email}")
                return True
            else:
                logger.error(f"Failed to send cancellation email: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"Error sending cancellation email: {str(e)}")
            return False 