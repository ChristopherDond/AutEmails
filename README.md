# 📬 Email Automation System

A comprehensive Python-based email automation system for sending reports, notifications, and scheduled emails automatically.

## ✨ Features

- **📧 Email Sending**: Send simple or HTML emails with attachments
- **📊 Report Generation**: Generate and send reports in HTML, CSV, or JSON format
- **🔔 Notifications**: Send instant notifications with priority levels and types
- **⏰ Email Scheduling**: Schedule emails using cron expressions or predefined intervals
- **🔒 Secure Configuration**: Environment-based configuration for sensitive data

## 📁 Project Structure

```
AutEmails/
├── main.py              # Main entry point
├── config.py            # Configuration settings
├── email_sender.py      # Core email sending functionality
├── reports.py           # Report generation and sending
├── notifications.py     # Notification system
├── scheduler.py         # Email scheduling system
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/ChristopherDond/AutEmails.git
cd AutEmails

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your SMTP settings
```

### 3. Run

```bash
# Run demo
python main.py demo

# Run scheduler service
python main.py service
```

## 📖 Usage

### Sending a Simple Email

```python
from email_sender import send_quick_email

send_quick_email(
    to="recipient@example.com",
    subject="Hello!",
    body="This is a test email."
)
```

### Sending an HTML Email with Attachments

```python
from email_sender import EmailSender

with EmailSender() as sender:
    sender.send_email(
        to=["user1@example.com", "user2@example.com"],
        subject="Monthly Report",
        body="<h1>Report</h1><p>Please see attached.</p>",
        html=True,
        attachments=["report.pdf", "data.csv"]
    )
```

### Generating and Sending Reports

```python
from reports import ReportGenerator, send_report

# Sample data
data = [
    {"Name": "John", "Sales": 150},
    {"Name": "Jane", "Sales": 230},
]

# Quick send
send_report(
    title="Sales Report",
    data=data,
    recipients=["manager@example.com"],
    format="html"
)

# Or use the generator directly
generator = ReportGenerator()
html = generator.generate_html_report("Sales Report", data)
generator.save_report(html, "sales", "html")
```

### Sending Notifications

```python
from notifications import (
    send_notification,
    send_alert,
    send_error_notification,
    send_success_notification
)

# Simple notification
send_notification(
    title="Update Available",
    message="A new version is available.",
    recipients="admin@example.com",
    priority="high",
    notification_type="info"
)

# Alert notification
send_alert(
    title="Server Down",
    message="Production server is not responding.",
    recipients=["admin@example.com", "devops@example.com"],
    server="prod-01",
    downtime="5 minutes"
)

# Success notification
send_success_notification(
    title="Deployment Complete",
    message="Version 2.0 deployed successfully.",
    recipients="team@example.com"
)
```

### Scheduling Emails

```python
from scheduler import (
    get_scheduler,
    schedule_email,
    schedule_daily_report,
    ScheduleInterval
)

# Schedule using predefined intervals
schedule_email(
    name="weekly_summary",
    recipients="team@example.com",
    subject="Weekly Summary",
    body_generator=lambda: "Here's your weekly summary...",
    schedule=ScheduleInterval.WEEKLY
)

# Schedule using cron expression
schedule_email(
    name="morning_greeting",
    recipients="team@example.com",
    subject="Good Morning!",
    body_generator=lambda: "Have a great day!",
    schedule="0 9 * * 1-5"  # 9 AM, Monday to Friday
)

# Schedule a daily report
schedule_daily_report(
    name="daily_metrics",
    recipients="management@example.com",
    subject="Daily Metrics",
    data_generator=lambda: [{"Metric": "Users", "Value": 1000}],
    hour=8
)

# Start the scheduler
scheduler = get_scheduler()
scheduler.start()
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP username/email | - |
| `SMTP_PASSWORD` | SMTP password/app password | - |
| `SMTP_USE_TLS` | Use TLS encryption | `True` |
| `DEFAULT_SENDER` | Default sender email | - |
| `TIMEZONE` | Timezone for scheduler | `America/Sao_Paulo` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Gmail Configuration

For Gmail, you need to:

1. Enable 2-Factor Authentication
2. Generate an App Password:
   - Go to Google Account → Security → App Passwords
   - Generate a new app password for "Mail"
3. Use the app password in `SMTP_PASSWORD`

## 📝 CLI Commands

```bash
# Run all demos
python main.py demo

# Send a quick email
python main.py send --to recipient@example.com --subject "Test" --body "Hello!"

# Send HTML email
python main.py send --to recipient@example.com --subject "Test" --body "<h1>Hello!</h1>" --html

# Demo report generation
python main.py report

# Demo notifications
python main.py notify

# Demo scheduler
python main.py schedule

# Run as scheduler service
python main.py service
```

## 🔧 Notification Types & Priorities

### Notification Types
- `info` - General information
- `success` - Success messages
- `warning` - Warning alerts
- `error` - Error notifications
- `alert` - Critical alerts

### Priority Levels
- `low` - Low priority (gray)
- `normal` - Normal priority (blue)
- `high` - High priority (yellow)
- `critical` - Critical priority (red)

## 📅 Cron Expression Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Examples

| Expression | Description |
|------------|-------------|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour |
| `0 9 * * *` | Every day at 9 AM |
| `0 9 * * 1-5` | Weekdays at 9 AM |
| `0 9 1 * *` | First of month at 9 AM |
| `*/5 * * * *` | Every 5 minutes |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**ChristopherDond**

- GitHub: [@ChristopherDond](https://github.com/ChristopherDond)

---

⭐ Star this repository if you found it helpful!
