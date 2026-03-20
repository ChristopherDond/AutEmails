"""
Email Scheduler Module
Schedule and automate email sending with cron-like scheduling.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import re

from email_sender import EmailSender, send_quick_email
from reports import ReportGenerator
from notifications import send_notification
from config import SCHEDULER_CONFIG, LOG_CONFIG

logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format=LOG_CONFIG["format"]
)
logger = logging.getLogger(__name__)


class ScheduleInterval(Enum):
    """Common schedule intervals."""
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduledEmail:
    """
    Scheduled email configuration.
    """
    name: str
    recipients: List[str]
    subject: str
    body_generator: Callable[[], str]
    schedule: str  # Cron expression or interval
    enabled: bool = True
    html: bool = False
    attachments_generator: Optional[Callable[[], List[str]]] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CronParser:
    """
    Simple cron expression parser.
    Supports: minute hour day month weekday
    Special characters: * (any), */n (every n), n-m (range), n,m (list)
    """
    
    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """Parse a single cron field."""
        if field == "*":
            return list(range(min_val, max_val + 1))
        
        if field.startswith("*/"):
            step = int(field[2:])
            return list(range(min_val, max_val + 1, step))
        
        if "-" in field:
            start, end = map(int, field.split("-"))
            return list(range(start, end + 1))
        
        if "," in field:
            return [int(x) for x in field.split(",")]
        
        return [int(field)]
    
    @staticmethod
    def parse(expression: str) -> Dict[str, List[int]]:
        """
        Parse a cron expression.
        
        Args:
            expression: Cron expression (minute hour day month weekday)
            
        Returns:
            Dict with parsed values for each field
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        
        return {
            "minutes": CronParser.parse_field(parts[0], 0, 59),
            "hours": CronParser.parse_field(parts[1], 0, 23),
            "days": CronParser.parse_field(parts[2], 1, 31),
            "months": CronParser.parse_field(parts[3], 1, 12),
            "weekdays": CronParser.parse_field(parts[4], 0, 6),  # 0 = Sunday
        }
    
    @staticmethod
    def matches(expression: str, dt: datetime) -> bool:
        """Check if a datetime matches a cron expression."""
        try:
            parsed = CronParser.parse(expression)
            return (
                dt.minute in parsed["minutes"]
                and dt.hour in parsed["hours"]
                and dt.day in parsed["days"]
                and dt.month in parsed["months"]
                and dt.weekday() in [d % 7 for d in parsed["weekdays"]]
            )
        except Exception:
            return False
    
    @staticmethod
    def next_run(expression: str, after: Optional[datetime] = None) -> datetime:
        """Calculate the next run time for a cron expression."""
        if after is None:
            after = datetime.now()
        
        # Start from next minute
        current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Search for next match (limit to prevent infinite loop)
        for _ in range(525600):  # Max 1 year of minutes
            if CronParser.matches(expression, current):
                return current
            current += timedelta(minutes=1)
        
        raise ValueError(f"Could not find next run time for: {expression}")


class EmailScheduler:
    """
    Schedule and manage automated email sending.
    """
    
    INTERVAL_CRON = {
        ScheduleInterval.MINUTELY: "* * * * *",
        ScheduleInterval.HOURLY: "0 * * * *",
        ScheduleInterval.DAILY: "0 9 * * *",  # 9 AM
        ScheduleInterval.WEEKLY: "0 9 * * 1",  # Monday 9 AM
        ScheduleInterval.MONTHLY: "0 9 1 * *",  # 1st of month 9 AM
    }
    
    def __init__(self):
        """Initialize EmailScheduler."""
        self._scheduled_emails: Dict[str, ScheduledEmail] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._email_sender = EmailSender()
    
    def add_scheduled_email(
        self,
        name: str,
        recipients: Union[str, List[str]],
        subject: str,
        body_generator: Callable[[], str],
        schedule: Union[str, ScheduleInterval],
        html: bool = False,
        attachments_generator: Optional[Callable[[], List[str]]] = None,
        **metadata
    ) -> ScheduledEmail:
        """
        Add a new scheduled email.
        
        Args:
            name: Unique name for the scheduled email
            recipients: Email recipient(s)
            subject: Email subject
            body_generator: Function that generates email body
            schedule: Cron expression or ScheduleInterval
            html: Whether body is HTML
            attachments_generator: Function that returns attachment paths
            **metadata: Additional metadata
            
        Returns:
            ScheduledEmail: The created scheduled email
        """
        if isinstance(recipients, str):
            recipients = [recipients]
        
        if isinstance(schedule, ScheduleInterval):
            schedule = self.INTERVAL_CRON[schedule]
        
        scheduled_email = ScheduledEmail(
            name=name,
            recipients=recipients,
            subject=subject,
            body_generator=body_generator,
            schedule=schedule,
            html=html,
            attachments_generator=attachments_generator,
            metadata=metadata
        )
        
        # Calculate next run
        scheduled_email.next_run = CronParser.next_run(schedule)
        
        self._scheduled_emails[name] = scheduled_email
        logger.info(f"Added scheduled email: {name}, next run: {scheduled_email.next_run}")
        return scheduled_email
    
    def remove_scheduled_email(self, name: str) -> bool:
        """Remove a scheduled email."""
        if name in self._scheduled_emails:
            del self._scheduled_emails[name]
            logger.info(f"Removed scheduled email: {name}")
            return True
        return False
    
    def enable(self, name: str) -> bool:
        """Enable a scheduled email."""
        if name in self._scheduled_emails:
            self._scheduled_emails[name].enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """Disable a scheduled email."""
        if name in self._scheduled_emails:
            self._scheduled_emails[name].enabled = False
            return True
        return False
    
    def _execute_scheduled_email(self, scheduled_email: ScheduledEmail) -> bool:
        """Execute a scheduled email."""
        try:
            # Generate body
            body = scheduled_email.body_generator()
            
            # Generate attachments
            attachments = None
            if scheduled_email.attachments_generator:
                attachments = scheduled_email.attachments_generator()
            
            # Send email
            success = send_quick_email(
                to=scheduled_email.recipients,
                subject=scheduled_email.subject,
                body=body,
                html=scheduled_email.html,
                attachments=attachments
            )
            
            if success:
                scheduled_email.last_run = datetime.now()
                scheduled_email.run_count += 1
                scheduled_email.next_run = CronParser.next_run(
                    scheduled_email.schedule,
                    scheduled_email.last_run
                )
                logger.info(f"Executed scheduled email: {scheduled_email.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing {scheduled_email.name}: {e}")
            return False
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()
            
            for name, scheduled_email in self._scheduled_emails.items():
                if not scheduled_email.enabled:
                    continue
                
                if scheduled_email.next_run and now >= scheduled_email.next_run:
                    self._execute_scheduled_email(scheduled_email)
            
            # Sleep for 30 seconds between checks
            time.sleep(30)
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("Email scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Email scheduler stopped")
    
    def run_now(self, name: str) -> bool:
        """Execute a scheduled email immediately."""
        if name in self._scheduled_emails:
            return self._execute_scheduled_email(self._scheduled_emails[name])
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "scheduled_emails": {
                name: {
                    "enabled": se.enabled,
                    "last_run": se.last_run.isoformat() if se.last_run else None,
                    "next_run": se.next_run.isoformat() if se.next_run else None,
                    "run_count": se.run_count,
                }
                for name, se in self._scheduled_emails.items()
            }
        }
    
    def list_scheduled(self) -> List[str]:
        """List all scheduled email names."""
        return list(self._scheduled_emails.keys())


# Global scheduler instance
_scheduler: Optional[EmailScheduler] = None


def get_scheduler() -> EmailScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = EmailScheduler()
    return _scheduler


def schedule_email(
    name: str,
    recipients: Union[str, List[str]],
    subject: str,
    body_generator: Callable[[], str],
    schedule: Union[str, ScheduleInterval],
    **kwargs
) -> ScheduledEmail:
    """
    Quick function to schedule an email.
    
    Args:
        name: Unique name
        recipients: Email recipient(s)
        subject: Email subject
        body_generator: Function that generates body
        schedule: Cron expression or ScheduleInterval
        **kwargs: Additional arguments
        
    Returns:
        ScheduledEmail: The scheduled email
    """
    scheduler = get_scheduler()
    return scheduler.add_scheduled_email(
        name, recipients, subject, body_generator, schedule, **kwargs
    )


def schedule_daily_report(
    name: str,
    recipients: Union[str, List[str]],
    subject: str,
    data_generator: Callable[[], List[Dict[str, Any]]],
    hour: int = 9
) -> ScheduledEmail:
    """
    Schedule a daily HTML report.
    
    Args:
        name: Report name
        recipients: Email recipient(s)
        subject: Email subject
        data_generator: Function that returns report data
        hour: Hour of day to send (0-23)
        
    Returns:
        ScheduledEmail: The scheduled report
    """
    generator = ReportGenerator()
    
    def body_gen():
        data = data_generator()
        return generator.generate_html_report(name, data)
    
    return schedule_email(
        name=name,
        recipients=recipients,
        subject=subject,
        body_generator=body_gen,
        schedule=f"0 {hour} * * *",
        html=True
    )


if __name__ == "__main__":
    # Example usage
    print("Email Scheduler Module")
    print("=" * 50)
    
    scheduler = EmailScheduler()
    
    # Add a test scheduled email
    scheduler.add_scheduled_email(
        name="daily_summary",
        recipients=["test@example.com"],
        subject="Daily Summary",
        body_generator=lambda: "This is your daily summary.",
        schedule=ScheduleInterval.DAILY
    )
    
    print("\nScheduled Emails:")
    for name in scheduler.list_scheduled():
        status = scheduler.get_status()["scheduled_emails"][name]
        print(f"  - {name}: next run at {status['next_run']}")
