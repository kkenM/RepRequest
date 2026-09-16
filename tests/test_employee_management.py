"""
Employee-management tests for RepRequest.

These tests verify that company administrators can create,
edit, and delete employee accounts while preserving expected
role and password behavior.
"""

from app.extensions import db
from app.models import User
from app.roles import (
    EMPLOYEE_CREW,
    EMPLOYEE_TECHNICIAN
)
from app.services import company_service


def login_admin(client):
    """
    Log in using the standard administrator test account.
    """

    return client.post(
        "/login",
        data={
            "email": "admin@test.com",
            "password": "password123"
        }
    )


def create_admin(app):
    """
    Create the standard administrator test account.
    """

    with app.app_context():
        company_service.create_company_with_admin(
            company_name="Test Company",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password="password123"
        )


def test_admin_can_create_employee(client, app):
    """
    Administrators should be able to create employee accounts.
    """

    # Arrange
    create_admin(app)
    login_admin(client)

    # Act
    response = client.post(
        "/admin/employees/create",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "password": "password123",
            "role": EMPLOYEE_CREW
        }
    )

    # Assert
    assert response.status_code == 302

    with app.app_context():
        employee = User.query.filter_by(
            email="jane@test.com"
        ).first()

        assert employee is not None
        assert employee.first_name == "Jane"
        assert employee.last_name == "Doe"
        assert employee.role == EMPLOYEE_CREW

        assert employee.company is not None
        assert employee.company.name == "Test Company"

        # Passwords should never be stored as plaintext.
        assert employee.password_hash != "password123"

        # The stored hash should still validate the original password.
        assert employee.check_password(
            "password123"
        )


def test_admin_can_change_employee_role(client, app):
    """
    Administrators should be able to change an employee's role.
    """

    # Arrange
    create_admin(app)
    login_admin(client)

    # Create an employee through the real route.
    client.post(
        "/admin/employees/create",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "password": "password123",
            "role": EMPLOYEE_CREW
        }
    )

    with app.app_context():
        employee = User.query.filter_by(
            email="jane@test.com"
        ).first()

        assert employee is not None

        employee_id = employee.id

    # Act
    response = client.post(
        f"/admin/employees/{employee_id}/edit",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "role": EMPLOYEE_TECHNICIAN
        }
    )

    # Assert
    assert response.status_code == 302

    with app.app_context():
        employee = db.session.get(
            User,
            employee_id
        )

        assert employee is not None
        assert employee.role == EMPLOYEE_TECHNICIAN


def test_admin_can_edit_employee_information(client, app):
    """
    Administrators should be able to update an employee's
    name and email address.
    """

    # Arrange
    create_admin(app)
    login_admin(client)

    client.post(
        "/admin/employees/create",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "password": "password123",
            "role": EMPLOYEE_CREW
        }
    )

    with app.app_context():
        employee = User.query.filter_by(
            email="jane@test.com"
        ).first()

        assert employee is not None

        employee_id = employee.id

    # Act
    response = client.post(
        f"/admin/employees/{employee_id}/edit",
        data={
            "first_name": "Janet",
            "last_name": "Smith",
            "email": "janet@test.com",
            "role": EMPLOYEE_CREW
        }
    )

    # Assert
    assert response.status_code == 302

    with app.app_context():
        employee = db.session.get(
            User,
            employee_id
        )

        assert employee is not None
        assert employee.first_name == "Janet"
        assert employee.last_name == "Smith"
        assert employee.email == "janet@test.com"


def test_admin_cannot_assign_invalid_employee_role(client, app):
    """
    Administrators should not be able to create an employee
    with an unsupported role.
    """

    # Arrange
    create_admin(app)
    login_admin(client)

    # Act
    response = client.post(
        "/admin/employees/create",
        data={
            "first_name": "Bad",
            "last_name": "Role",
            "email": "badrole@test.com",
            "password": "password123",
            "role": "company-admin"
        }
    )

    # Assert
    assert response.status_code == 200

    with app.app_context():
        employee = User.query.filter_by(
            email="badrole@test.com"
        ).first()

        assert employee is None

    assert b"Invalid employee role" in response.data


def test_admin_cannot_create_duplicate_email(client, app):
    """
    Administrators should not be able to create two accounts
    that use the same email address.
    """

    # Arrange
    create_admin(app)
    login_admin(client)

    client.post(
        "/admin/employees/create",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "password": "password123",
            "role": EMPLOYEE_CREW
        }
    )

    # Act
    response = client.post(
        "/admin/employees/create",
        data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "jane@test.com",
            "password": "different-password",
            "role": EMPLOYEE_TECHNICIAN
        }
    )

    # Assert
    assert response.status_code == 200

    assert (
        b"An account with that email already exists."
        in response.data
    )

    with app.app_context():
        matching_users = User.query.filter_by(
            email="jane@test.com"
        ).all()

        assert len(matching_users) == 1


def test_admin_can_delete_employee(client, app):
    """
    Administrators should be able to delete an employee
    belonging to their company.
    """

    # Arrange
    create_admin(app)
    login_admin(client)

    client.post(
        "/admin/employees/create",
        data={
            "first_name": "Delete",
            "last_name": "Me",
            "email": "delete@test.com",
            "password": "password123",
            "role": EMPLOYEE_CREW
        }
    )

    with app.app_context():
        employee = User.query.filter_by(
            email="delete@test.com"
        ).first()

        assert employee is not None

        employee_id = employee.id

    # Act
    response = client.post(
        f"/admin/employees/{employee_id}/delete"
    )

    # Assert
    assert response.status_code == 302

    with app.app_context():
        employee = db.session.get(
            User,
            employee_id
        )

        assert employee is None