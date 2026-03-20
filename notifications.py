"""
Notification System Module
Send instant notifications via email for alerts, updates, and events.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import time

from email_sender import send_quick_email
from config import NOTIFICATION_CONFIG

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"


@dataclass
class Notification:
    """
    Notification data class.
    """
    title: str
    message: str
    recipients: List[str]
    priority: NotificationPriority = NotificationPriority.NORMAL
    notification_type: NotificationType = NotificationType.INFO
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    sent: bool = False


class NotificationManager:
    """
    Manage and send notifications via email.
    """
    
    PRIORITY_COLORS = {
        NotificationPriority.LOW: "#6c757d",
        NotificationPriority.NORMAL: "#17a2b8",
        NotificationPriority.HIGH: "#ffc107",
        NotificationPriority.CRITICAL: "#dc3545",
    }
    
    TYPE_ICONS = {
        NotificationType.INFO: "ℹ️",
        NotificationType.SUCCESS: "✅",
        NotificationType.WARNING: "⚠️",
        NotificationType.ERROR: "❌",
        NotificationType.ALERT: "🚨",
    }
    
    def __init__(self):
        """Initialize NotificationManager."""
        self.max_retries = NOTIFICATION_CONFIG["max_retries"]
        self.retry_delay = NOTIFICATION_CONFIG["retry_delay"]
        self._notification_history: List[Notification] = []
    
    def create_notification(
        self,
        title: str,
        message: str,
        recipients: Union[str, List[str]],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        notification_type: NotificationType = NotificationType.INFO,
        **metadata
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            title: Notification title
            message: Notification message
            recipients: Email recipient(s)
            priority: Priority level
            notification_type: Type of notification
            **metadata: Additional metadata
            
        Returns:
            Notification: Created notification object
        """
        if isinstance(recipients, str):
            recipients = [recipients]
        
        notification = Notification(
            title=title,
            message=message,
            recipients=recipients,
            priority=priority,
            notification_type=notification_type,
            metadata=metadata
        )
        
        self._notification_history.append(notification)
        logger.info(f"Notification created: {title}")
        return notification
    
    def _generate_html(self, notification: Notification) -> str:
        """Generate HTML content for notification email."""
        color = self.PRIORITY_COLORS.get(notification.priority, "#17a2b8")
        icon = self.TYPE_ICONS.get(notification.notification_type, "ℹ️")
        
        metadata_html = ""
        if notification.metadata:
            items = "".join(
                f"<li><strong>{key}:</strong> {value}</li>"
                for key, value in notification.metadata.items()
            )
            metadata_html = f"<hr><h4>Details:</h4><ul>{items}</ul>"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .notification {{ background-color: white; border-radius: 8px; padding: 20px; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ border-left: 4px solid {color}; padding-left: 15px; margin-bottom: 20px; }}
        .title {{ margin: 0; color: #333; font-size: 24px; }}
        .priority {{ display: inline-block; padding: 4px 12px; background-color: {color}; color: white; border-radius: 4px; font-size: 12px; margin-top: 8px; }}
        .message {{ color: #555; line-height: 1.6; margin: 20px 0; }}
        .footer {{ color: #888; font-size: 12px; border-top: 1px solid #eee; padding-top: 15px; margin-top: 20px; }}
        h4 {{ color: #333; margin-bottom: 10px; }}
        ul {{ color: #555; }}
    </style>
</head>
<body>
    <div class="notification">
        <div class="header">
            <h1 class="title">{icon} {notification.title}</h1>
            <span class="priority">{notification.priority.value.upper()}</span>
        </div>
        <div class="message">
            {notification.message.replace(chr(10), '<br>')}
        </div>
        {metadata_html}
        <div class="footer">
            <p>Notification Type: {notification.notification_type.value.capitalize()}</p>
            <p>Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    def send(self, notification: Notification) -> bool:
        """
        Send a notification via email.
        
        Args:
            notification: Notification to send
            
        Returns:
            bool: True if sent successfully
        """
        html_content = self._generate_html(notification)
        
        for attempt in range(self.max_retries):
            try:
                success = send_quick_email(
                    to=notification.recipients,
                    subject=f"[{notification.priority.value.upper()}] {notification.title}",
                    body=html_content,
                    html=True
                )
                
                if success:
                    notification.sent = True
                    notification.sent_at = datetime.now()
                    logger.info("Notification sent: %s", notification.title)
                    return True

            except Exception:
                logger.warning("Attempt %s failed", attempt + 1, exc_info=True)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        logger.error(
            "Failed to send notification after %s attempts", self.max_retries
        )
        return False
    
    def send_immediate(
        self,
        title: str,
        message: str,
        recipients: Union[str, List[str]],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        notification_type: NotificationType = NotificationType.INFO,
        **metadata
    ) -> bool:
        """
        Create and send a notification immediately.
        
        Args:
            title: Notification title
            message: Notification message
            recipients: Email recipient(s)
            priority: Priority level
            notification_type: Type of notification
            **metadata: Additional metadata
            
        Returns:
            bool: True if sent successfully
        """
        notification = self.create_notification(
            title, message, recipients, priority, notification_type, **metadata
        )
        return self.send(notification)
    
    def get_history(self, sent_only: bool = False) -> List[Notification]:
        """
        Get notification history.
        
        Args:
            sent_only: If True, return only sent notifications
            
        Returns:
            List[Notification]: List of notifications
        """
        if sent_only:
            return [n for n in self._notification_history if n.sent]
        return self._notification_history.copy()


def send_notification(
    title: str,
    message: str,
    recipients: Union[str, List[str]],
    priority: str = "normal",
    notification_type: str = "info"
) -> bool:
    """
    Quick function to send a notification.
    
    Args:
        title: Notification title
        message: Notification message
        recipients: Email recipient(s)
        priority: Priority level (low, normal, high, critical)
        notification_type: Type (info, success, warning, error, alert)
        
    Returns:
        bool: True if sent successfully
    """
    manager = NotificationManager()
    return manager.send_immediate(
        title=title,
        message=message,
        recipients=recipients,
        priority=NotificationPriority(priority),
        notification_type=NotificationType(notification_type)
    )


def send_alert(
    title: str,
    message: str,
    recipients: Union[str, List[str]],
    **metadata
) -> bool:
    """Send a high-priority alert notification."""
    manager = NotificationManager()
    return manager.send_immediate(
        title=title,
        message=message,
        recipients=recipients,
        priority=NotificationPriority.HIGH,
        notification_type=NotificationType.ALERT,
        **metadata
    )


def send_error_notification(
    title: str,
    message: str,
    recipients: Union[str, List[str]],
    **metadata
) -> bool:
    """Send an error notification."""
    manager = NotificationManager()
    return manager.send_immediate(
        title=title,
        message=message,
        recipients=recipients,
        priority=NotificationPriority.HIGH,
        notification_type=NotificationType.ERROR,
        **metadata
    )


def send_success_notification(
    title: str,
    message: str,
    recipients: Union[str, List[str]],
    **metadata
) -> bool:
    """Send a success notification."""
    manager = NotificationManager()
    return manager.send_immediate(
        title=title,
        message=message,
        recipients=recipients,
        priority=NotificationPriority.NORMAL,
        notification_type=NotificationType.SUCCESS,
        **metadata
    )


if __name__ == "__main__":
    print("Notification System Module")
    print("=" * 50)
    
    manager = NotificationManager()
    notification = manager.create_notification(
        title="Test Notification",
        message="This is a test notification message.",
        recipients=["test@example.com"],
        priority=NotificationPriority.HIGH,
        notification_type=NotificationType.INFO,
        source="Test Script",
        event_id="12345"
    )
    
    print(f"Created notification: {notification.title}")
    print(f"Priority: {notification.priority.value}")
    print(f"Type: {notification.notification_type.value}")
