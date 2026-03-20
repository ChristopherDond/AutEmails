"""
Core Email Sender Module
Handles SMTP connection and email sending functionality.
"""
import logging
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Union

from config import DEFAULT_SENDER, SMTP_CONFIG

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Core email sender class for sending emails via SMTP.
    """
    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        timeout: Optional[float] = None,
    ):
        """
        Initialize EmailSender with SMTP configuration.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            use_tls: Whether to use TLS encryption
        """
        self.smtp_server = smtp_server or SMTP_CONFIG["server"]
        self.smtp_port = smtp_port or SMTP_CONFIG["port"]
        self.username = username or SMTP_CONFIG["username"]
        self.password = password or SMTP_CONFIG["password"]
        self.use_tls = use_tls if use_tls is not None else SMTP_CONFIG["use_tls"]
        self.timeout = SMTP_CONFIG.get("timeout", 30) if timeout is None else timeout
        self._connection: Optional[smtplib.SMTP] = None

    @staticmethod
    def _normalize_addresses(value: Optional[Union[str, List[str]]]) -> List[str]:
        if not value:
            return []
        items = [value] if isinstance(value, str) else list(value)
        cleaned: List[str] = []
        seen: set[str] = set()
        for item in items:
            addr = str(item).strip()
            if not addr or addr in seen:
                continue
            seen.add(addr)
            cleaned.append(addr)
        return cleaned

    def connect(self) -> bool:
        """Establish connection to SMTP server."""
        try:
            self._connection = smtplib.SMTP(
                self.smtp_server,
                self.smtp_port,
                timeout=self.timeout,
            )
            self._connection.ehlo()
            if self.use_tls:
                self._connection.starttls(context=ssl.create_default_context())
                self._connection.ehlo()
            if self.username and self.password:
                self._connection.login(self.username, self.password)
            logger.info("Connected to SMTP server: %s", self.smtp_server)
            return True
        except Exception:
            logger.error("Failed to connect to SMTP server", exc_info=True)
            self._connection = None
            return False
    
    def disconnect(self):
        """Close SMTP connection."""
        if self._connection:
            try:
                self._connection.quit()
                logger.info("Disconnected from SMTP server")
            except Exception:
                logger.warning("Error disconnecting", exc_info=True)
            finally:
                self._connection = None
    
    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body content
            from_addr: Sender email address
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            html: Whether body is HTML content
            attachments: List of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            to_list = self._normalize_addresses(to)
            cc_list = self._normalize_addresses(cc)
            bcc_list = self._normalize_addresses(bcc)

            if not to_list:
                logger.error("No recipients provided (to=empty)")
                return False

            msg = MIMEMultipart()
            msg["From"] = from_addr or DEFAULT_SENDER
            msg["To"] = ", ".join(to_list)
            msg["Subject"] = subject

            if cc_list:
                msg["Cc"] = ", ".join(cc_list)

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, str(file_path))

            recipients: List[str] = [*to_list, *cc_list, *bcc_list]

            if not self._connection and not self.connect():
                return False
            if not self._connection:
                return False

            self._connection.sendmail(msg["From"], recipients, msg.as_string())
            logger.info("Email sent successfully to: %s", msg["To"])
            return True

        except Exception:
            logger.error("Failed to send email", exc_info=True)
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to the email message."""
        path = Path(file_path)
        if not path.exists():
            logger.warning("Attachment not found: %s", file_path)
            return
        
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={path.name}"
        )
        msg.attach(part)
        logger.debug("Attached file: %s", path.name)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def send_quick_email(
    to: Union[str, List[str]],
    subject: str,
    body: str,
    **kwargs
) -> bool:
    """
    Quick function to send an email without managing connection.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        body: Email body content
        **kwargs: Additional arguments passed to send_email
        
    Returns:
        bool: True if email sent successfully
    """
    with EmailSender() as sender:
        return sender.send_email(to, subject, body, **kwargs)


if __name__ == "__main__":
    print("Email Sender Module")
    print("Use EmailSender class or send_quick_email function to send emails.")
