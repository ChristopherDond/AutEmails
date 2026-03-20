"""
Report Generator and Email Module
Generates reports and sends them via email.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import json
import csv
import io

from email_sender import EmailSender, send_quick_email
from config import REPORT_CONFIG, LOG_CONFIG

logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format=LOG_CONFIG["format"]
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate reports in various formats and send via email.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize ReportGenerator.
        
        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir or REPORT_CONFIG["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(
        self,
        title: str,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        template: Optional[str] = None
    ) -> str:
        """
        Generate an HTML report.
        
        Args:
            title: Report title
            data: List of dictionaries containing report data
            columns: Column headers (auto-detected if not provided)
            template: Custom HTML template
            
        Returns:
            str: HTML content
        """
        if not columns and data:
            columns = list(data[0].keys())
        
        if template:
            return template.format(title=title, data=data)
        
        # Default HTML template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #ddd; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <table>
        <thead>
            <tr>
                {"".join(f"<th>{col}</th>" for col in (columns or []))}
            </tr>
        </thead>
        <tbody>
"""
        for row in data:
            html += "            <tr>\n"
            for col in (columns or []):
                html += f"                <td>{row.get(col, '')}</td>\n"
            html += "            </tr>\n"
        
        html += f"""
        </tbody>
    </table>
    <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>
"""
        return html
    
    def generate_csv_report(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        """
        Generate a CSV report.
        
        Args:
            data: List of dictionaries containing report data
            columns: Column headers
            
        Returns:
            str: CSV content
        """
        if not columns and data:
            columns = list(data[0].keys())
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns or [])
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    def generate_json_report(self, data: Any, pretty: bool = True) -> str:
        """
        Generate a JSON report.
        
        Args:
            data: Data to convert to JSON
            pretty: Whether to format with indentation
            
        Returns:
            str: JSON content
        """
        return json.dumps(data, indent=2 if pretty else None, default=str)
    
    def save_report(
        self,
        content: str,
        filename: str,
        format: str = "html"
    ) -> Path:
        """
        Save report to file.
        
        Args:
            content: Report content
            filename: Base filename (without extension)
            format: File format (html, csv, json)
            
        Returns:
            Path: Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.{format}"
        file_path = self.output_dir / full_filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Report saved: {file_path}")
        return file_path
    
    def generate_and_send(
        self,
        title: str,
        data: List[Dict[str, Any]],
        recipients: List[str],
        format: str = "html",
        save_copy: bool = True,
        email_body: Optional[str] = None
    ) -> bool:
        """
        Generate a report and send it via email.
        
        Args:
            title: Report title
            data: Report data
            recipients: Email recipients
            format: Report format (html, csv, json)
            save_copy: Whether to save a local copy
            email_body: Custom email body text
            
        Returns:
            bool: True if sent successfully
        """
        # Generate report
        if format == "html":
            content = self.generate_html_report(title, data)
        elif format == "csv":
            content = self.generate_csv_report(data)
        elif format == "json":
            content = self.generate_json_report(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save local copy
        attachment_path = None
        if save_copy:
            attachment_path = self.save_report(content, title.replace(" ", "_"), format)
        
        # Prepare email
        if format == "html":
            body = email_body or content
            is_html = True
        else:
            body = email_body or f"Please find the attached {title} report."
            is_html = False
        
        # Send email
        attachments = [str(attachment_path)] if attachment_path and format != "html" else None
        
        return send_quick_email(
            to=recipients,
            subject=f"Report: {title}",
            body=body,
            html=is_html,
            attachments=attachments
        )


class ScheduledReport:
    """
    Configuration for a scheduled report.
    """
    
    def __init__(
        self,
        name: str,
        data_source: Callable[[], List[Dict[str, Any]]],
        recipients: List[str],
        schedule: str,  # cron-like expression
        format: str = "html"
    ):
        self.name = name
        self.data_source = data_source
        self.recipients = recipients
        self.schedule = schedule
        self.format = format
        self.last_run = None
        self.enabled = True


def send_report(
    title: str,
    data: List[Dict[str, Any]],
    recipients: List[str],
    format: str = "html"
) -> bool:
    """
    Quick function to generate and send a report.
    
    Args:
        title: Report title
        data: Report data
        recipients: Email recipients
        format: Report format
        
    Returns:
        bool: True if sent successfully
    """
    generator = ReportGenerator()
    return generator.generate_and_send(title, data, recipients, format)


if __name__ == "__main__":
    # Example usage
    sample_data = [
        {"Name": "John Doe", "Email": "john@example.com", "Status": "Active"},
        {"Name": "Jane Smith", "Email": "jane@example.com", "Status": "Pending"},
        {"Name": "Bob Wilson", "Email": "bob@example.com", "Status": "Active"},
    ]
    
    generator = ReportGenerator()
    html_report = generator.generate_html_report("User Report", sample_data)
    print("Sample HTML Report Generated:")
    print(html_report[:500] + "...")
