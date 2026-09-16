"""
Role and authorization tests for RepRequest.
"""

from app.services import (
    company_service,
    user_service
)
from app.roles import EMPLOYEE_CREW


def login(client, email, password):
    """
    Authenticate a user through the real login route.
    """

    return client.post(
        "/login",
        data={
            "email": email,
            "password": password
        }
    )


def test_admin_can_access_admin_dashboard(
    client,
    app
):
    """
    Company administrators should be allowed to access
    company-administration routes.
    """

    with app.app_context():

        company_service.create_company_with_admin(
            company_name="Test Company",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password="password123"
        )

    login(
        client,
        "admin@test.com",
        "password123"
    )

    response = client.get(
        "/admin/"
    )

    assert response.status_code == 200


def test_employee_cannot_access_admin_dashboard(
    client,
    app
):
    """
    Standard employees should receive HTTP 403 when
    attempting to access administrator functionality.
    """

    with app.app_context():

        company, admin = (
            company_service.create_company_with_admin(
                company_name="Test Company",
                first_name="Admin",
                last_name="User",
                email="admin@test.com",
                password="password123"
            )
        )

        user_service.create_employee(
            company_id=company.id,
            first_name="Crew",
            last_name="User",
            email="crew@test.com",
            password="password123",
            role=EMPLOYEE_CREW
        )

    login(
        client,
        "crew@test.com",
        "password123"
    )

    response = client.get(
        "/admin/"
    )

    assert response.status_code == 403