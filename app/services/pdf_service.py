from typing import List
from datetime import date
from jinja2 import Template
from app.schemas.reservation import ReservationWithTables
import io
import logging

logger = logging.getLogger(__name__)


class PDFService:
    def __init__(self):
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Daily Reservations - {{ date.strftime('%A, %B %d, %Y') }}</title>
            <style>
                @page {
                    size: A4;
                    margin: 1cm;
                }
                
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                    margin: 0;
                    padding: 0;
                }
                
                .reservation-slip {
                    border: 2px solid #333;
                    margin-bottom: 20px;
                    padding: 15px;
                    page-break-inside: avoid;
                    position: relative;
                }
                
                .cut-line {
                    border-top: 1px dashed #999;
                    margin: 10px 0;
                    page-break-after: always;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                }
                
                .logo {
                    width: 60px;
                    height: 60px;
                    object-fit: contain;
                }
                
                .header-text {
                    text-align: center;
                }
                
                .restaurant-name {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }
                
                .date-time {
                    font-size: 14px;
                    color: #7f8c8d;
                }
                
                .customer-info {
                    margin-bottom: 15px;
                }
                
                .customer-name {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }
                
                .contact-info {
                    color: #34495e;
                    margin-bottom: 5px;
                }
                
                .reservation-details {
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }
                
                .detail-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 5px;
                }
                
                .detail-label {
                    font-weight: bold;
                    color: #2c3e50;
                }
                
                .detail-value {
                    color: #34495e;
                }
                
                .tables-info {
                    background-color: #e8f4fd;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }
                
                .notes {
                    background-color: #fff3cd;
                    padding: 10px;
                    border-radius: 5px;
                    border-left: 4px solid #ffc107;
                }
                
                .notes-label {
                    font-weight: bold;
                    color: #856404;
                    margin-bottom: 5px;
                }
                
                .footer {
                    text-align: center;
                    margin-top: 15px;
                    font-size: 10px;
                    color: #7f8c8d;
                }
                
                .page-break {
                    page-break-before: always;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <img src="data:image/png;base64,{{ logo_base64 }}" alt="The Castle Pub Logo" class="logo">
                <div class="header-text">
                    <div class="restaurant-name">The Castle Pub</div>
                    <div class="date-time">Daily Reservations - {{ date.strftime('%A, %B %d, %Y') }}</div>
                </div>
            </div>
            
            {% for reservation in reservations %}
            <div class="reservation-slip">
                <div class="customer-info">
                    <div class="customer-name">{{ reservation.customer_name }}</div>
                    <div class="contact-info">{{ reservation.email }}</div>
                    <div class="contact-info">{{ reservation.phone }}</div>
                </div>
                
                <div class="reservation-details">
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{{ reservation.date.strftime('%A, %B %d, %Y') }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{{ reservation.time.strftime('%I:%M %p') }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Party Size:</span>
                        <span class="detail-value">{{ reservation.party_size }} people</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Room:</span>
                        <span class="detail-value">{{ reservation.room_name }}</span>
                    </div>
                </div>
                
                {% if reservation.tables %}
                <div class="tables-info">
                    <div class="detail-label">Assigned Tables:</div>
                    {% for table in reservation.tables %}
                    <div class="detail-row">
                        <span>{{ table.table_name }}</span>
                        <span>({{ table.capacity }} seats)</span>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if reservation.notes %}
                <div class="notes">
                    <div class="notes-label">Special Notes:</div>
                    <div>{{ reservation.notes }}</div>
                </div>
                {% endif %}
                
                <div class="footer">
                    Reservation ID: {{ reservation.id }} | Generated: {{ generated_at }}
                </div>
            </div>
            
            {% if not loop.last %}
            <div class="cut-line"></div>
            {% endif %}
            {% endfor %}
        </body>
        </html>
        """

    def generate_daily_pdf(self, reservations: List[ReservationWithTables], target_date: date) -> bytes:
        """Generate PDF with daily reservation slips"""
        try:
            from datetime import datetime
            import base64
            import os
            
            # Load and encode logo
            logo_base64 = ""
            # Try multiple possible paths for the logo
            possible_logo_paths = [
                "static/logo.png",
                "/app/static/logo.png",
                os.path.join(os.getcwd(), "static", "logo.png"),
                os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.png")
            ]
            
            logo_found = False
            for logo_path in possible_logo_paths:
                if os.path.exists(logo_path):
                    try:
                        with open(logo_path, "rb") as logo_file:
                            logo_data = logo_file.read()
                            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                        logger.info(f"Logo loaded successfully from {logo_path}")
                        logo_found = True
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load logo from {logo_path}: {e}")
                        continue
            
            if not logo_found:
                logger.warning("Logo file not found in any expected location, PDF will be generated without logo")
            
            # Render HTML template
            template = Template(self.html_template)
            html_content = template.render(
                reservations=reservations,
                date=target_date,
                generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                logo_base64=logo_base64
            )
            
            # For now, return HTML content as bytes (PDF generation disabled for Windows)
            logger.info(f"Generated HTML for {target_date} with {len(reservations)} reservations")
            return html_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error generating daily PDF: {str(e)}")
            raise

    def generate_reservation_slip(self, reservation: ReservationWithTables) -> bytes:
        """Generate a single reservation slip PDF"""
        try:
            from datetime import datetime
            import base64
            import os
            
            # Load and encode logo
            logo_base64 = ""
            # Try multiple possible paths for the logo
            possible_logo_paths = [
                "static/logo.png",
                "/app/static/logo.png",
                os.path.join(os.getcwd(), "static", "logo.png"),
                os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.png")
            ]
            
            logo_found = False
            for logo_path in possible_logo_paths:
                if os.path.exists(logo_path):
                    try:
                        with open(logo_path, "rb") as logo_file:
                            logo_data = logo_file.read()
                            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                        logger.info(f"Logo loaded successfully from {logo_path}")
                        logo_found = True
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load logo from {logo_path}: {e}")
                        continue
            
            if not logo_found:
                logger.warning("Logo file not found in any expected location, PDF will be generated without logo")
            
            # Render HTML template for single reservation
            template = Template(self.html_template)
            html_content = template.render(
                reservations=[reservation],
                date=reservation.date,
                generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                logo_base64=logo_base64
            )
            
            # For now, return HTML content as bytes (PDF generation disabled for Windows)
            logger.info(f"Generated HTML for reservation {reservation.id}")
            return html_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error generating reservation slip PDF: {str(e)}")
            raise 