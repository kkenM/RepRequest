"""
Outgoing email for RepRequest.

Without MAIL_SERVER configured, messages are stored in
sent_messages and printed to the terminal instead of sent.
Tests and local development rely on this.
"""

import smtplib
from email.message import EmailMessage

from flask import current_app, url_for


# Messages "sent" while MAIL_SERVER is unset.
sent_messages = []


def send_email(to, subject, body):
    """
    Send one plain-text email.

    Raises OSError (smtplib errors included) if sending fails.
    """

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["MAIL_FROM"]
    message["To"] = to
    message.set_content(body)

    server = current_app.config.get("MAIL_SERVER")

    if not server:
        sent_messages.append(message)
        current_app.logger.warning(
            "Email not sent (MAIL_SERVER is not set):\n%s",
            message
        )
        return

    with smtplib.SMTP(
        server,
        current_app.config["MAIL_PORT"],
        timeout=10
    ) as smtp:
        smtp.starttls()
        smtp.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"]
        )
        smtp.send_message(message)


def send_welcome_email(user, temporary_password):
    """
    Email a new employee their username and temporary password.
    """

    login_url = url_for("auth.login", _external=True)

    send_email(
        to=user.email,
        subject="Your RepRequest account",
        body=(
            f"Hi {user.first_name},\n\n"
            f"{user.company.name} created a RepRequest account for you.\n\n"
            f"Sign in at: {login_url}\n"
            f"Username: {user.username}\n"
            f"Temporary password: {temporary_password}\n\n"
            "You'll be asked to choose your own password when you sign in.\n"
        )
    )


def send_password_reset_email(user, reset_url):
    """
    Email a one-time password reset link.
    """

    send_email(
        to=user.email,
        subject="Reset your RepRequest password",
        body=(
            f"Hi {user.first_name},\n\n"
            f"Use this link to choose a new password:\n{reset_url}\n\n"
            "The link expires in 1 hour and works once. "
            "If you didn't ask for this, you can ignore this email.\n"
        )
    )


def send_urgent_repair_email(user, repair_request):
    """
    Tell a technician that a high-severity repair request was filed.
    """

    machine = repair_request.machine
    reporter = repair_request.reported_by

    queue_url = url_for("repairs.index", _external=True)

    send_email(
        to=user.email,
        subject=f"High severity: {machine.name} needs repair",
        body=(
            f"Hi {user.first_name},\n\n"
            "A high-severity repair request was filed.\n\n"
            f"Machine: {machine.name}\n"
            f"Reported by: {reporter.first_name} {reporter.last_name}\n\n"
            f"{repair_request.description}\n\n"
            f"Open the repair queue: {queue_url}\n"
        )
    )


def send_assignment_email(user, repair_request, assigned_by):
    """
    Tell a technician that an administrator assigned them a request.
    """

    machine = repair_request.machine

    queue_url = url_for("repairs.index", view="mine", _external=True)

    send_email(
        to=user.email,
        subject=f"Assigned to you: {machine.name}",
        body=(
            f"Hi {user.first_name},\n\n"
            f"{assigned_by.first_name} {assigned_by.last_name} assigned "
            "you a repair request.\n\n"
            f"Machine: {machine.name}\n"
            f"Severity: {repair_request.severity_label}\n\n"
            f"{repair_request.description}\n\n"
            f"Your assigned requests: {queue_url}\n"
        )
    )
