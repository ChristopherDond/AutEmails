"""
Email Scheduler Module
Schedule and automate email sending with cron-like scheduling.
"""
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Union

from email_sender import EmailSender
from reports import ReportGenerator

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
    schedule: str
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
    def parse_field(field: str, min_val: int, max_val: int) -> frozenset[int]:
        if field == "*":
            return frozenset(range(min_val, max_val + 1))

        if field.startswith("*/"):
            step = int(field[2:])
            return frozenset(range(min_val, max_val + 1, step))

        if "-" in field:
            start, end = map(int, field.split("-"))
            return frozenset(range(start, end + 1))

        if "," in field:
            return frozenset(int(x) for x in field.split(","))

        return frozenset({int(field)})
    
    @staticmethod
    @lru_cache(maxsize=256)
    def parse(expression: str) -> Dict[str, frozenset[int]]:
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
        
        minutes = CronParser.parse_field(parts[0], 0, 59)
        hours = CronParser.parse_field(parts[1], 0, 23)
        days = CronParser.parse_field(parts[2], 1, 31)
        months = CronParser.parse_field(parts[3], 1, 12)
        raw_weekdays = CronParser.parse_field(parts[4], 0, 7)
        weekdays = frozenset(d % 7 for d in raw_weekdays)

        return {
            "minutes": minutes,
            "hours": hours,
            "days": days,
            "months": months,
            "weekdays": weekdays,
        }
    
    @staticmethod
    def matches(expression: str, dt: datetime) -> bool:
        try:
            parsed = CronParser.parse(expression)
            return (
                dt.minute in parsed["minutes"]
                and dt.hour in parsed["hours"]
                and dt.day in parsed["days"]
                and dt.month in parsed["months"]
                and dt.weekday() in parsed["weekdays"]
            )
        except Exception:
            return False
    
    @staticmethod
    def next_run(expression: str, after: Optional[datetime] = None) -> datetime:
        if after is None:
            after = datetime.now()

        parsed = CronParser.parse(expression)
        current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        for _ in range(525600):
            if (
                current.minute in parsed["minutes"]
                and current.hour in parsed["hours"]
                and current.day in parsed["days"]
                and current.month in parsed["months"]
                and current.weekday() in parsed["weekdays"]
            ):
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
        ScheduleInterval.DAILY: "0 9 * * *",
        ScheduleInterval.WEEKLY: "0 9 * * 1",
        ScheduleInterval.MONTHLY: "0 9 1 * *",
    }
    
    def __init__(self):
        """Initialize EmailScheduler."""
        self._scheduled_emails: Dict[str, ScheduledEmail] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._email_sender = EmailSender()
        self._lock = threading.RLock()
        self._wakeup = threading.Event()
    
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
        
        scheduled_email.next_run = CronParser.next_run(schedule)

        with self._lock:
            self._scheduled_emails[name] = scheduled_email
        self._wakeup.set()
        logger.info("Added scheduled email: %s, next run: %s", name, scheduled_email.next_run)
        return scheduled_email
    
    def remove_scheduled_email(self, name: str) -> bool:
        """Remove a scheduled email."""
        with self._lock:
            removed = self._scheduled_emails.pop(name, None)
        if removed is not None:
            self._wakeup.set()
            logger.info("Removed scheduled email: %s", name)
            return True
        return False
    
    def enable(self, name: str) -> bool:
        """Enable a scheduled email."""
        with self._lock:
            scheduled = self._scheduled_emails.get(name)
            if scheduled is None:
                return False
            scheduled.enabled = True
        self._wakeup.set()
        return True
    
    def disable(self, name: str) -> bool:
        """Disable a scheduled email."""
        with self._lock:
            scheduled = self._scheduled_emails.get(name)
            if scheduled is None:
                return False
            scheduled.enabled = False
        self._wakeup.set()
        return True
    
    def _execute_scheduled_email(self, scheduled_email: ScheduledEmail) -> bool:
        """Execute a scheduled email."""
        try:
            body = scheduled_email.body_generator()

            attachments = None
            if scheduled_email.attachments_generator:
                attachments = scheduled_email.attachments_generator()

            success = self._email_sender.send_email(
                to=scheduled_email.recipients,
                subject=scheduled_email.subject,
                body=body,
                html=scheduled_email.html,
                attachments=attachments,
            )

            if success:
                run_time = datetime.now()
                next_run = CronParser.next_run(scheduled_email.schedule, run_time)
                with self._lock:
                    scheduled_email.last_run = run_time
                    scheduled_email.run_count += 1
                    scheduled_email.next_run = next_run
                self._wakeup.set()
                logger.info("Executed scheduled email: %s", scheduled_email.name)

            return success

        except Exception:
            logger.error("Error executing %s", scheduled_email.name, exc_info=True)
            return False
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()

            due: List[ScheduledEmail] = []
            soonest_next: Optional[datetime] = None

            with self._lock:
                for scheduled_email in self._scheduled_emails.values():
                    if not scheduled_email.enabled or not scheduled_email.next_run:
                        continue

                    if now >= scheduled_email.next_run:
                        due.append(scheduled_email)
                        continue

                    if soonest_next is None or scheduled_email.next_run < soonest_next:
                        soonest_next = scheduled_email.next_run

            for scheduled_email in due:
                self._execute_scheduled_email(scheduled_email)

            if not self._running:
                break

            timeout = 30.0
            if soonest_next is not None:
                delta = (soonest_next - datetime.now()).total_seconds()
                timeout = 1.0 if delta <= 0 else min(300.0, max(1.0, delta))

            self._wakeup.wait(timeout=timeout)
            self._wakeup.clear()
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._wakeup.clear()
        if not self._email_sender.connect():
            logger.warning("Could not connect to SMTP on scheduler start")
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("Email scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        self._wakeup.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._email_sender.disconnect()
        logger.info("Email scheduler stopped")
    
    def run_now(self, name: str) -> bool:
        """Execute a scheduled email immediately."""
        with self._lock:
            scheduled = self._scheduled_emails.get(name)
        if scheduled is None:
            return False
        return self._execute_scheduled_email(scheduled)
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        with self._lock:
            scheduled_snapshot = dict(self._scheduled_emails)

        return {
            "running": self._running,
            "scheduled_emails": {
                name: {
                    "enabled": se.enabled,
                    "last_run": se.last_run.isoformat() if se.last_run else None,
                    "next_run": se.next_run.isoformat() if se.next_run else None,
                    "run_count": se.run_count,
                }
                for name, se in scheduled_snapshot.items()
            },
        }
    
    def list_scheduled(self) -> List[str]:
        """List all scheduled email names."""
        with self._lock:
            return list(self._scheduled_emails.keys())


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
    print("Email Scheduler Module")
    print("=" * 50)
    
    scheduler = EmailScheduler()
    
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
