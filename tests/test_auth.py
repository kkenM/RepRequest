"""
Authentication tests for RepRequest.
"""

from app.models import User
from app.services import company_service


def test_company_registration(client, app):
    """
    Registering a company should create both the Company
    and its initial administrator account.
    """

    response = client.post(
        "/register",
        data={
            "company_name": "Test Company",
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 302

    with app.app_context():

        user = User.query.filter_by(
            email="admin@test.com"
        ).first()

        assert user is not None
        assert user.company is not None
        assert user.company.name == "Test Company"
        assert user.is_company_admin


def test_valid_login(client, app):
    """
    A user with valid credentials should be able to log in.
    """

    with app.app_context():

        company_service.create_company_with_admin(
            company_name="Test Company",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password="password123"
        )

    response = client.post(
        "/login",
        data={
            "email": "admin@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 302


def test_invalid_login(client, app):
    """
    Incorrect credentials should not authenticate the user.
    """

    with app.app_context():

        company_service.create_company_with_admin(
            company_name="Test Company",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password="password123"
        )

    response = client.post(
        "/login",
        data={
            "email": "admin@test.com",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 200

    assert b"Invalid email or password" in response.data