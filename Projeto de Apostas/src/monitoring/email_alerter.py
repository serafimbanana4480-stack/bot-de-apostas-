"""
Email alerter — sends critical alerts and daily reports via SMTP.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

logger = logging.getLogger("email_alerter")

LEVEL_COLORS = {
    "CRITICAL": "#FF0000",
    "WARNING": "#FFA500",
    "INFO": "#0066CC",
}


class EmailAlerter:
    """Sends alerts and daily reports via SMTP email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        to_address: str = "",
        from_address: Optional[str] = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.to_address = to_address
        self.from_address = from_address or smtp_user

    def send_alert(
        self,
        level: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a critical/warning alert email."""
        if not self.to_address:
            logger.warning("No email recipient configured — skipping alert email")
            return

        color = LEVEL_COLORS.get(level, "#333333")
        subject = f"[VBQ {level}] {title}"

        # HTML body
        html = f"""
        <html><body>
        <div style="border-left: 4px solid {color}; padding: 12px; margin: 10px 0;">
            <h2 style="color: {color};">{level}: {title}</h2>
            <p>{message}</p>
        """
        if data:
            html += "<table style='border-collapse: collapse; margin-top: 10px;'>"
            for k, v in data.items():
                html += f"<tr><td style='padding: 4px 12px; font-weight: bold;'>{k}</td><td style='padding: 4px 12px;'>{v}</td></tr>"
            html += "</table>"

        html += """
        <hr style="margin-top: 20px;">
        <p style="color: #999; font-size: 12px;">VBQ Alert System</p>
        </div></body></html>
        """

        self._send_email(subject, html)

    def send_daily_report(self, report_data: Dict[str, Any]) -> None:
        """Send a daily summary report email."""
        if not self.to_address:
            return

        subject = "[VBQ] Daily Report"

        html = """
        <html><body>
        <h2>VBQ Daily Report</h2>
        <table style="border-collapse: collapse; width: 100%;">
        """
        for k, v in report_data.items():
            html += f"<tr><td style='padding: 8px; border: 1px solid #ddd; font-weight: bold;'>{k}</td>"
            html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{v}</td></tr>"

        html += """
        </table>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">VBQ Automated Report</p>
        </body></html>
        """

        self._send_email(subject, html)

    def _send_email(self, subject: str, html_body: str) -> None:
        """Send an HTML email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = self.to_address

        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_address, [self.to_address], msg.as_string())
            logger.info("Email sent: %s", subject)
        except Exception as e:
            logger.error("Failed to send email: %s", e)
