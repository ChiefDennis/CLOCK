import smtplib
from email.mime.text import MIMEText
from flask import current_app
from models import Alarm
from extensions import db

def send_alarm_email(subject, body):
    """Constructs and sends an email alarm."""
    
    # Load config from the current Flask app instance
    sender = current_app.config.get("MAIL_USERNAME")
    recipient = current_app.config.get("MAIL_RECIPIENT")
    password = current_app.config.get("MAIL_PASSWORD")
    server_host = current_app.config.get("MAIL_SERVER")
    server_port = current_app.config.get("MAIL_PORT")
    use_tls = current_app.config.get("MAIL_USE_TLS")

    if not all([sender, recipient, password, server_host, server_port]):
        print("[Email ERROR] Mail configuration is incomplete. Cannot send email.")
        return

    # Create the email message
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        print(f"Sending alarm email to {recipient}...")
        # Connect to the SMTP server
        with smtplib.SMTP(server_host, server_port) as server:
            if use_tls:
                server.starttls()  # Secure the connection
            server.login(sender, password)
            server.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print(f"[Email ERROR] Failed to send email: {e}")

def raise_alarm(severity, event_type, message):
    """Creates a new alarm record in the database."""
    print(f"RAISING ALARM [${severity}]: ${message}")
    try:
        alarm = Alarm(
            severity=severity,
            event_type=event_type,
            message=message
        )
        db.session.add(alarm)
        db.session.commit()
        # Optional, trigger an immediate email here
        send_alarm_email(f"Security Alarm [{severity}]: {event_type}", message)
    except Exception as e:
        print(f"[Alarm ERROR] Failed to record alarm to database: {e}")
        db.session.rollback()