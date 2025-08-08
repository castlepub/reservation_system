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

                .reserved-banner {
                    text-align: center;
                    font-size: 18px;
                    font-weight: 900;
                    color: #c0392b;
                    letter-spacing: 2px;
                    margin-bottom: 6px;
                }
                
                .customer-name {
                    font-size: 14px;
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

                .time-strong {
                    font-weight: 800;
                    font-size: 12px;
                }
                
                .tables-info {
                    background-color: #e8f4fd;
                    padding: 3px;
                    border-radius: 3px;
                    margin-bottom: 3px;
                    font-size: 10px;
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
                <div class="reserved-banner">RESERVED</div>
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
                        <span class="detail-value time-strong">{{ reservation.time.strftime('%I:%M %p') }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Size:</span>
                        <span class="detail-value">{{ reservation.party_size }}</span>
                    </div>
                    {% if reservation.room_name %}
                    <div class="detail-row">
                        <span class="detail-label">Room:</span>
                        <span class="detail-value">{{ reservation.room_name }}</span>
                    </div>
                    {% endif %}
                </div>
                
                {% if reservation.tables %}
                <div class="tables-info">
                    <div class="detail-label">Table:</div>
                    {% for table in reservation.tables %}
                    <div class="detail-row">
                        <span>{{ table.table_name }}</span>
                        {% if table.capacity %}<span>({{ table.capacity }})</span>{% endif %}
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
            # Try WeasyPrint first; fall back to ReportLab if unavailable in the environment
            try:
                from weasyprint import HTML  # type: ignore
            except Exception as weasy_err:  # pragma: no cover
                HTML = None  # type: ignore
            
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

            if HTML is not None:
                try:
                    pdf_bytes = HTML(string=html_content).write_pdf()
                    logger.info(f"Generated PDF for {target_date} with {len(reservations)} reservations (WeasyPrint)")
                    return pdf_bytes
                except Exception as e:  # pragma: no cover
                    logger.warning(f"WeasyPrint failed, falling back to ReportLab: {e}")

            # Fallback: generate PDF with ReportLab (pure Python)
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib import colors
                from reportlab.lib.units import mm
                from reportlab.lib.utils import ImageReader
                import io

                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                page_width, page_height = A4

                # Header with logo and date
                y = page_height - 20 * mm
                if logo_base64:
                    try:
                        logo_bytes = base64.b64decode(logo_base64)
                        c.drawImage(ImageReader(io.BytesIO(logo_bytes)), 15 * mm, y - 12 * mm, width=12 * mm, height=12 * mm, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass
                c.setFont("Helvetica-Bold", 12)
                c.drawString(30 * mm, y - 6 * mm, "The Castle Pub - Daily Reservations")
                c.setFont("Helvetica", 9)
                c.drawString(30 * mm, y - 11 * mm, target_date.strftime('%A, %B %d, %Y'))

                # Grid: 2 columns x 5 rows per page
                top_margin = y - 16 * mm
                left_margin = 10 * mm
                right_margin = 10 * mm
                bottom_margin = 10 * mm
                cols = 2
                rows = 5
                gap = 4 * mm
                card_width = (page_width - left_margin - right_margin - gap) / cols
                card_height = (top_margin - bottom_margin - (rows - 1) * gap) / rows

                def draw_reservation_card(ix: int, reservation: ReservationWithTables):
                    col = ix % cols
                    row = ix // cols
                    if row >= rows:
                        return False
                    x = left_margin + col * (card_width + gap)
                    y0 = top_margin - row * (card_height + gap)
                    # Border
                    c.setLineWidth(1)
                    c.setStrokeColor(colors.black)
                    c.setFillColor(colors.whitesmoke)
                    c.roundRect(x, y0 - card_height, card_width, card_height, 4 * mm, stroke=1, fill=1)

                    # RESERVED banner
                    c.setFillColor(colors.HexColor("#c0392b"))
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(x + card_width / 2, y0 - 8 * mm, "RESERVED")

                    # Customer name
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica-Bold", 12)
                    c.drawCentredString(x + card_width / 2, y0 - 15 * mm, (reservation.customer_name or ""))

                    # Details
                    text_x = x + 6 * mm
                    line_y = y0 - 22 * mm
                    c.setFont("Helvetica", 9)
                    c.drawString(text_x, line_y, f"Date: {reservation.date.strftime('%m/%d') if hasattr(reservation.date, 'strftime') else ''}")
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(text_x + 60, line_y, f"Time: {reservation.time.strftime('%I:%M %p') if hasattr(reservation.time, 'strftime') else ''}")
                    c.setFont("Helvetica", 9)
                    c.drawString(text_x, line_y - 5 * mm, f"Size: {getattr(reservation, 'party_size', '')}")
                    room_name = getattr(reservation, 'room_name', None) or ""
                    if room_name:
                        c.drawString(text_x + 60, line_y - 5 * mm, f"Room: {room_name}")

                    # Tables
                    table_y = line_y - 11 * mm
                    tables = getattr(reservation, 'tables', []) or []
                    if tables:
                        c.setFont("Helvetica-Bold", 9)
                        c.drawString(text_x, table_y, "Table:")
                        c.setFont("Helvetica", 9)
                        names = ", ".join([t.get('table_name') if isinstance(t, dict) else getattr(t, 'table_name', '') for t in tables])
                        c.drawString(text_x + 30, table_y, names[:50])

                    # Notes
                    notes = getattr(reservation, 'notes', None) or ""
                    if notes:
                        c.setFont("Helvetica-Oblique", 8)
                        c.setFillColor(colors.HexColor('#856404'))
                        c.drawString(text_x, table_y - 6 * mm, f"Notes: {notes[:80]}")
                        c.setFillColor(colors.black)

                    # Footer
                    c.setFont("Helvetica", 7)
                    c.setFillColor(colors.gray)
                    c.drawRightString(x + card_width - 4 * mm, y0 - card_height + 4 * mm, f"ID: {str(getattr(reservation, 'id', ''))[:8]}")
                    c.setFillColor(colors.black)
                    return True

                # Draw up to 10 per page
                idx_on_page = 0
                for i, r in enumerate(reservations):
                    if idx_on_page >= cols * rows:
                        c.showPage()
                        # draw header again for new page
                        y = page_height - 20 * mm
                        if logo_base64:
                            try:
                                logo_bytes = base64.b64decode(logo_base64)
                                c.drawImage(ImageReader(io.BytesIO(logo_bytes)), 15 * mm, y - 12 * mm, width=12 * mm, height=12 * mm, preserveAspectRatio=True, mask='auto')
                            except Exception:
                                pass
                        c.setFont("Helvetica-Bold", 12)
                        c.drawString(30 * mm, y - 6 * mm, "The Castle Pub - Daily Reservations")
                        c.setFont("Helvetica", 9)
                        c.drawString(30 * mm, y - 11 * mm, target_date.strftime('%A, %B %d, %Y'))
                        top_margin = y - 16 * mm
                        idx_on_page = 0
                    if draw_reservation_card(idx_on_page, r):
                        idx_on_page += 1

                c.showPage()
                c.save()
                buffer.seek(0)
                logger.info(f"Generated PDF for {target_date} with {len(reservations)} reservations (ReportLab)")
                return buffer.read()
            except Exception as re_err:  # pragma: no cover
                logger.error(f"ReportLab PDF generation failed: {re_err}")
                raise
            
        except Exception as e:
            logger.error(f"Error generating daily PDF: {str(e)}")
            raise

    def generate_reservation_slip(self, reservation: ReservationWithTables) -> bytes:
        """Generate a single reservation slip PDF"""
        try:
            from datetime import datetime
            import base64
            import os
            from weasyprint import HTML
            
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
            
            # Try WeasyPrint first; fall back to ReportLab
            try:
                from weasyprint import HTML  # type: ignore
            except Exception:
                HTML = None  # type: ignore

            # Render HTML template for single reservation
            template = Template(self.html_template)
            html_content = template.render(
                reservations=[reservation],
                date=reservation.date,
                generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                logo_base64=logo_base64
            )

            if HTML is not None:
                try:
                    pdf_bytes = HTML(string=html_content).write_pdf()
                    logger.info(f"Generated PDF for reservation {reservation.id} (WeasyPrint)")
                    return pdf_bytes
                except Exception as e:  # pragma: no cover
                    logger.warning(f"WeasyPrint failed for slip, falling back to ReportLab: {e}")

            # Fallback: ReportLab single slip
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib import colors
                from reportlab.lib.units import mm
                from reportlab.lib.utils import ImageReader
                import io, base64

                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                page_width, page_height = A4

                # Header
                y = page_height - 20 * mm
                if logo_base64:
                    try:
                        logo_bytes = base64.b64decode(logo_base64)
                        c.drawImage(ImageReader(io.BytesIO(logo_bytes)), 15 * mm, y - 12 * mm, width=12 * mm, height=12 * mm, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass
                c.setFont("Helvetica-Bold", 12)
                c.drawString(30 * mm, y - 6 * mm, "The Castle Pub - Reservation Slip")

                # Card area
                x = 15 * mm
                y0 = y - 16 * mm
                card_width = page_width - 30 * mm
                card_height = 60 * mm
                c.setFillColor(colors.whitesmoke)
                c.roundRect(x, y0 - card_height, card_width, card_height, 4 * mm, stroke=1, fill=1)

                c.setFillColor(colors.HexColor("#c0392b"))
                c.setFont("Helvetica-Bold", 18)
                c.drawCentredString(x + card_width / 2, y0 - 8 * mm, "RESERVED")

                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(x + card_width / 2, y0 - 16 * mm, (reservation.customer_name or ""))

                text_x = x + 8 * mm
                line_y = y0 - 24 * mm
                c.setFont("Helvetica", 11)
                c.drawString(text_x, line_y, f"Date: {reservation.date.strftime('%m/%d') if hasattr(reservation.date, 'strftime') else ''}")
                c.setFont("Helvetica-Bold", 12)
                c.drawString(text_x + 80, line_y, f"Time: {reservation.time.strftime('%I:%M %p') if hasattr(reservation.time, 'strftime') else ''}")
                c.setFont("Helvetica", 11)
                c.drawString(text_x, line_y - 6 * mm, f"Size: {getattr(reservation, 'party_size', '')}")
                room_name = getattr(reservation, 'room_name', None) or ""
                if room_name:
                    c.drawString(text_x + 80, line_y - 6 * mm, f"Room: {room_name}")

                tables = getattr(reservation, 'tables', []) or []
                if tables:
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(text_x, line_y - 12 * mm, "Table:")
                    c.setFont("Helvetica", 11)
                    names = ", ".join([t.get('table_name') if isinstance(t, dict) else getattr(t, 'table_name', '') for t in tables])
                    c.drawString(text_x + 35, line_y - 12 * mm, names[:60])

                c.showPage()
                c.save()
                buffer.seek(0)
                logger.info(f"Generated PDF for reservation {reservation.id} (ReportLab)")
                return buffer.read()
            except Exception as re_err:  # pragma: no cover
                logger.error(f"ReportLab slip generation failed: {re_err}")
                raise
            
        except Exception as e:
            logger.error(f"Error generating reservation slip PDF: {str(e)}")
            raise 