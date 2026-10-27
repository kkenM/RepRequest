"""
Tests for generated usernames, emailed temporary passwords,
forced password changes and password reset by email.
"""

import re
from urllib.parse import urlsplit

from app.models import User
from app.roles import EMPLOYEE_CREW
from app.services import (
    company_service,
    email_service,
    user_service
)


def login(client, identifier, password):
    return client.post(
        "/login",
        data={"login": identifier, "password": password}
    )


def create_admin(app):
    with app.app_context():
        company, admin = company_service.create_company_with_admin(
            company_name="Test Company",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password="password123"
        )

        return company.id


def last_email_body():
    return email_service.sent_messages[-1].get_content()


def create_jane_through_admin(client):
    """
    Create Jane Doe through the real admin route and return the
    username and temporary password from her welcome email.
    """

    login(client, "admin@test.com", "password123")

    client.post(
        "/admin/employees/create",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@gmail.com",
            "role": EMPLOYEE_CREW
        }
    )

    client.post("/logout")

    body = last_email_body()
    username = re.search(r"Username: (\S+)", body).group(1)
    password = re.search(r"Temporary password: (\S+)", body).group(1)

    return username, password


def test_username_is_initial_last_name_and_two_digits(app):
    username = user_service.generate_username("Jane", "Doe")

    assert re.fullmatch(r"jdoe\d{2}", username)


def test_username_strips_accents_and_punctuation(app):
    username = user_service.generate_username("José", "O'Brien")

    assert re.fullmatch(r"jobrien\d{2}", username)


def test_temporary_password_is_16_random_characters():
    first = user_service.generate_temporary_password()
    second = user_service.generate_temporary_password()

    assert len(first) == 16
    assert first != second


def test_two_jane_does_get_different_usernames(app):
    company_id = create_admin(app)

    first, _ = user_service.create_employee_with_temporary_password(
        company_id=company_id,
        first_name="Jane",
        last_name="Doe",
        email="jane1@gmail.com",
        role=EMPLOYEE_CREW
    )
    second, _ = user_service.create_employee_with_temporary_password(
        company_id=company_id,
        first_name="Jane",
        last_name="Doe",
        email="jane2@gmail.com",
        role=EMPLOYEE_CREW
    )

    assert first.username != second.username


def test_admin_create_emails_username_and_temporary_password(client, app):
    create_admin(app)

    username, password = create_jane_through_admin(client)

    assert len(email_service.sent_messages) == 1
    assert email_service.sent_messages[0]["To"] == "jane@gmail.com"

    employee = User.query.filter_by(email="jane@gmail.com").first()

    assert employee.username == username
    assert employee.must_change_password
    assert employee.check_password(password)


def test_admin_still_signs_in_with_email(client, app):
    create_admin(app)

    login(client, "admin@test.com", "password123")

    assert client.get("/dashboard").status_code == 200


def test_temporary_password_forces_password_change(client, app):
    create_admin(app)
    username, password = create_jane_through_admin(client)

    login(client, username, password)

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/account/password")


def test_changing_temporary_password(client, app):
    create_admin(app)
    username, password = create_jane_through_admin(client)

    login(client, username, password)

    client.post(
        "/account/password",
        data={
            "current_password": password,
            "new_password": "my-new-password",
            "confirm_password": "my-new-password"
        }
    )

    # The dashboard opens now.
    assert client.get("/dashboard").status_code == 200

    client.post("/logout")

    # The temporary password no longer works; the new one does.
    assert login(client, username, password).status_code == 200
    assert login(client, username, "my-new-password").status_code == 302


def test_forgot_password_for_unknown_account_sends_nothing(client, app):
    response = client.post(
        "/forgot-password",
        data={"login": "nobody42"}
    )

    assert response.status_code == 302
    assert email_service.sent_messages == []


def test_reset_link_works_once(client, app):
    create_admin(app)

    client.post(
        "/forgot-password",
        data={"login": "admin@test.com"}
    )

    reset_url = re.search(r"(http\S+/reset-password/\S+)", last_email_body()).group(1)
    reset_path = urlsplit(reset_url).path

    form = {
        "new_password": "reset-password-1",
        "confirm_password": "reset-password-1"
    }

    first = client.post(reset_path, data=form)
    assert first.headers["Location"].endswith("/login")

    second = client.post(reset_path, data=form)
    assert second.headers["Location"].endswith("/forgot-password")

    assert login(client, "admin@test.com", "reset-password-1").status_code == 302


def test_made_up_reset_token_is_rejected(client, app):
    response = client.get("/reset-password/not-a-real-token")

    assert response.headers["Location"].endswith("/forgot-password")