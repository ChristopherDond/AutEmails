"""
Email Automation Configuration
Configure your SMTP settings and email preferences here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration
SMTP_CONFIG = {
    "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", 587)),
    "username": os.getenv("SMTP_USERNAME", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "use_tls": os.getenv("SMTP_USE_TLS", "True").lower() == "true",
}

# Default sender
DEFAULT_SENDER = os.getenv("DEFAULT_SENDER", "noreply@example.com")

# Report settings
REPORT_CONFIG = {
    "output_dir": "reports",
    "default_format": "pdf",  # pdf, html, csv
}

# Notification settings
NOTIFICATION_CONFIG = {
    "max_retries": 3,
    "retry_delay": 5,  # seconds
}

# Scheduler settings
SCHEDULER_CONFIG = {
    "timezone": os.getenv("TIMEZONE", "America/Sao_Paulo"),
    "log_file": "logs/scheduler.log",
}

# Logging
LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/email_automation.log",
}
