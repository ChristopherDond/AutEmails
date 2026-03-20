"""
Email Automation Configuration
Configure your SMTP settings and email preferences here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_CONFIG = {
    "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", 587)),
    "username": os.getenv("SMTP_USERNAME", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "use_tls": os.getenv("SMTP_USE_TLS", "True").lower() == "true",
    "timeout": float(os.getenv("SMTP_TIMEOUT", 30)),
}

DEFAULT_SENDER = os.getenv("DEFAULT_SENDER", "noreply@example.com")

REPORT_CONFIG = {
    "output_dir": "reports",
    "default_format": os.getenv("REPORT_DEFAULT_FORMAT", "pdf"),
}

NOTIFICATION_CONFIG = {
    "max_retries": int(os.getenv("NOTIFICATION_MAX_RETRIES", 3)),
    "retry_delay": int(os.getenv("NOTIFICATION_RETRY_DELAY", 5)),
}

SCHEDULER_CONFIG = {
    "timezone": os.getenv("TIMEZONE", "America/Sao_Paulo"),
    "log_file": os.getenv("SCHEDULER_LOG_FILE", "logs/scheduler.log"),
}

LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    ),
    "file": os.getenv("LOG_FILE", "logs/email_automation.log"),
}
