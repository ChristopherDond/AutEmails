"""
Email Automation System - Main Entry Point
A comprehensive email automation system for sending reports, notifications, and scheduled emails.
"""
import argparse
import logging
from typing import List, Dict, Any

from email_sender import EmailSender, send_quick_email
from reports import ReportGenerator, send_report
from notifications import (
    NotificationManager,
    send_notification,
    send_alert,
    send_error_notification,
    send_success_notification,
    NotificationPriority,
    NotificationType
)
from scheduler import (
    EmailScheduler,
    get_scheduler,
    schedule_email,
    schedule_daily_report,
    ScheduleInterval
)
from config import LOG_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format=LOG_CONFIG["format"],
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_CONFIG["file"], encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def demo_send_email():
    """Demonstrate sending a simple email."""
    print("\n📧 Demo: Sending Simple Email")
    print("-" * 40)
    
    # Using context manager
    with EmailSender() as sender:
        success = sender.send_email(
            to="recipient@example.com",
            subject="Test Email",
            body="This is a test email sent from the Email Automation System."
        )
        print(f"Email sent: {success}")


def demo_send_report():
    """Demonstrate generating and sending a report."""
    print("\n📊 Demo: Sending Report")
    print("-" * 40)
    
    # Sample data
    data = [
        {"ID": 1, "Product": "Widget A", "Sales": 150, "Revenue": "$1,500"},
        {"ID": 2, "Product": "Widget B", "Sales": 230, "Revenue": "$2,300"},
        {"ID": 3, "Product": "Widget C", "Sales": 89, "Revenue": "$890"},
        {"ID": 4, "Product": "Widget D", "Sales": 312, "Revenue": "$3,120"},
    ]
    
    generator = ReportGenerator()
    
    # Generate HTML report
    html_report = generator.generate_html_report("Sales Report", data)
    print(f"Generated HTML report ({len(html_report)} characters)")
    
    # Save report
    saved_path = generator.save_report(html_report, "sales_report", "html")
    print(f"Saved to: {saved_path}")


def demo_send_notification():
    """Demonstrate sending notifications."""
    print("\n🔔 Demo: Sending Notification")
    print("-" * 40)
    
    manager = NotificationManager()
    
    # Create notification
    notification = manager.create_notification(
        title="System Update Available",
        message="A new system update is available for your server.\nPlease review and apply at your earliest convenience.",
        recipients=["admin@example.com"],
        priority=NotificationPriority.HIGH,
        notification_type=NotificationType.INFO,
        server="Production-01",
        update_version="2.5.0"
    )
    
    print(f"Created notification: {notification.title}")
    print(f"Priority: {notification.priority.value}")
    print(f"Recipients: {notification.recipients}")


def demo_scheduler():
    """Demonstrate email scheduling."""
    print("\n⏰ Demo: Email Scheduler")
    print("-" * 40)
    
    scheduler = get_scheduler()
    
    # Schedule a daily email
    scheduled = schedule_email(
        name="daily_greeting",
        recipients=["team@example.com"],
        subject="Good Morning Team!",
        body_generator=lambda: "Have a productive day!",
        schedule=ScheduleInterval.DAILY
    )
    
    print(f"Scheduled email: {scheduled.name}")
    print(f"Next run: {scheduled.next_run}")
    
    # Schedule a daily report
    def get_daily_data():
        return [
            {"Metric": "Active Users", "Value": 1250},
            {"Metric": "New Signups", "Value": 45},
            {"Metric": "Revenue", "Value": "$5,230"},
        ]
    
    report = schedule_daily_report(
        name="daily_metrics",
        recipients=["management@example.com"],
        subject="Daily Metrics Report",
        data_generator=get_daily_data,
        hour=8
    )
    
    print(f"Scheduled report: {report.name}")
    print(f"Next run: {report.next_run}")
    
    # Show status
    print("\nScheduler Status:")
    status = scheduler.get_status()
    for name, info in status["scheduled_emails"].items():
        print(f"  - {name}: next run at {info['next_run']}")


def run_scheduler_service():
    """Run the scheduler as a service."""
    print("\n🚀 Starting Email Scheduler Service")
    print("-" * 40)
    print("Press Ctrl+C to stop")
    
    scheduler = get_scheduler()
    
    # Example: Add some scheduled emails
    scheduler.add_scheduled_email(
        name="heartbeat",
        recipients=["admin@example.com"],
        subject="System Heartbeat",
        body_generator=lambda: f"System is running normally.",
        schedule="*/5 * * * *"  # Every 5 minutes
    )
    
    try:
        scheduler.start()
        # Keep running
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Email Automation System - Send reports, notifications, and scheduled emails"
    )
    
    parser.add_argument(
        "command",
        choices=["demo", "send", "report", "notify", "schedule", "service"],
        nargs="?",
        default="demo",
        help="Command to run"
    )
    
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Email body")
    parser.add_argument("--html", action="store_true", help="Send as HTML")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("📬 Email Automation System")
    print("=" * 50)
    
    if args.command == "demo":
        demo_send_email()
        demo_send_report()
        demo_send_notification()
        demo_scheduler()
    
    elif args.command == "send":
        if not all([args.to, args.subject, args.body]):
            print("Error: --to, --subject, and --body are required for send command")
            return
        
        success = send_quick_email(
            to=args.to,
            subject=args.subject,
            body=args.body,
            html=args.html
        )
        print(f"Email sent: {success}")
    
    elif args.command == "report":
        demo_send_report()
    
    elif args.command == "notify":
        demo_send_notification()
    
    elif args.command == "schedule":
        demo_scheduler()
    
    elif args.command == "service":
        run_scheduler_service()
    
    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
