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
                    margin: 0.5cm;
                }
                
                body {
                    font-family: Arial, sans-serif;
                    font-size: 8px;
                    line-height: 1.2;
                    margin: 0;
                    padding: 0;
                }
                
                .page-header {
                    text-align: center;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 5px;
                }
                
                .logo {
                    width: 30px;
                    height: 30px;
                    object-fit: contain;
                }
                
                .header-text {
                    text-align: center;
                }
                
                .restaurant-name {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 2px;
                }
                
                .date-time {
                    font-size: 10px;
                    color: #7f8c8d;
                }
                
                .reservations-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 5px;
                    page-break-inside: avoid;
                }
                
                .reservation-slip {
                    border: 1px solid #333;
                    padding: 8px;
                    page-break-inside: avoid;
                    position: relative;
                    background-color: #f9f9f9;
                    min-height: 120px;
                }
                
                .customer-name {
                    font-size: 10px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 3px;
                    text-align: center;
                    background-color: #e8f4fd;
                    padding: 2px;
                    border-radius: 3px;
                }
                
                .contact-info {
                    color: #34495e;
                    margin-bottom: 2px;
                    font-size: 7px;
                }
                
                .reservation-details {
                    background-color: #ffffff;
                    padding: 5px;
                    border-radius: 3px;
                    margin-bottom: 5px;
                    border: 1px solid #ddd;
                }
                
                .detail-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 2px;
                    font-size: 7px;
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
                    padding: 3px;
                    border-radius: 3px;
                    margin-bottom: 3px;
                    font-size: 6px;
                }
                
                .notes {
                    background-color: #fff3cd;
                    padding: 3px;
                    border-radius: 3px;
                    border-left: 2px solid #ffc107;
                    font-size: 6px;
                }
                
                .notes-label {
                    font-weight: bold;
                    color: #856404;
                    margin-bottom: 2px;
                }
                
                .footer {
                    text-align: center;
                    margin-top: 5px;
                    font-size: 6px;
                    color: #7f8c8d;
                }
                
                .page-break {
                    page-break-before: always;
                }
                
                /* Ensure 5 rows per page */
                .page {
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                .page-content {
                    flex: 1;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    grid-template-rows: repeat(5, 1fr);
                    gap: 5px;
                }
            </style>
        </head>
        <body>
            <div class="page-header">
                <img src="data:image/png;base64,{{ logo_base64 }}" alt="The Castle Pub Logo" class="logo">
                <div class="header-text">
                    <div class="restaurant-name">The Castle Pub</div>
                    <div class="date-time">Daily Reservations - {{ date.strftime('%A, %B %d, %Y') }}</div>
                </div>
            </div>
            
            <div class="page-content">
            {% for reservation in reservations %}
            <div class="reservation-slip">
                <div class="customer-name">{{ reservation.customer_name }}</div>
                <div class="contact-info">{{ reservation.email }}</div>
                <div class="contact-info">{{ reservation.phone }}</div>
                
                <div class="reservation-details">
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{{ reservation.date.strftime('%m/%d') }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{{ reservation.time.strftime('%I:%M %p') }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Size:</span>
                        <span class="detail-value">{{ reservation.party_size }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Room:</span>
                        <span class="detail-value">{{ reservation.room_name }}</span>
                    </div>
                </div>
                
                {% if reservation.tables %}
                <div class="tables-info">
                    <div class="detail-label">Tables:</div>
                    {% for table in reservation.tables %}
                    <div class="detail-row">
                        <span>{{ table.table_name }}</span>
                        <span>({{ table.capacity }})</span>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if reservation.notes %}
                <div class="notes">
                    <div class="notes-label">Notes:</div>
                    <div>{{ reservation.notes[:50] }}{% if reservation.notes|length > 50 %}...{% endif %}</div>
                </div>
                {% endif %}
                
                <div class="footer">
                    ID: {{ reservation.id[:8] }} | {{ generated_at }}
                </div>
            </div>
            {% endfor %}
            </div>
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
                os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.png"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "logo.png"),
                "/app/app/static/logo.png",
                "app/static/logo.png"
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
                # List all files in static directory for debugging
                static_dirs = ["static", "/app/static", "app/static"]
                for static_dir in static_dirs:
                    if os.path.exists(static_dir):
                        try:
                            files = os.listdir(static_dir)
                            logger.info(f"Files in {static_dir}: {files}")
                        except Exception as e:
                            logger.warning(f"Could not list files in {static_dir}: {e}")
            
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