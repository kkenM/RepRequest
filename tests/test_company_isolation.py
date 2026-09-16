"""
Multi-company data-isolation tests for RepRequest.

These tests verify that one company's administrator cannot
view, edit, or delete employees belonging to another company.
"""

from app.roles import EMPLOYEE_CREW
from app.services import (
    company_service,
    user_service
)


def test_admin_cannot_edit_other_company_employee(
    client,
    app
):
    """
    Company A's administrator must not be able to access
    Company B's employee-editing route.
    """

    with app.app_context():

        company_a, admin_a = (
            company_service.create_company_with_admin(
                company_name="Company A",
                first_name="Admin",
                last_name="A",
                email="admin-a@test.com",
                password="password123"
            )
        )

        company_b, admin_b = (
            company_service.create_company_with_admin(
                company_name="Company B",
                first_name="Admin",
                last_name="B",
                email="admin-b@test.com",
                password="password123"
            )
        )

        employee_b = user_service.create_employee(
            company_id=company_b.id,
            first_name="Employee",
            last_name="B",
            email="employee-b@test.com",
            password="password123",
            role=EMPLOYEE_CREW
        )

        employee_b_id = employee_b.id

    client.post(
        "/login",
        data={
            "email": "admin-a@test.com",
            "password": "password123"
        }
    )

    response = client.get(
        f"/admin/employees/{employee_b_id}/edit"
    )

    assert response.status_code == 404


def test_admin_cannot_delete_other_company_employee(
    client,
    app
):
    """
    Company A's administrator must not be able to delete
    an employee belonging to Company B.
    """

    with app.app_context():

        company_a, admin_a = (
            company_service.create_company_with_admin(
                company_name="Company A",
                first_name="Admin",
                last_name="A",
                email="admin-a@test.com",
                password="password123"
            )
        )

        company_b, admin_b = (
            company_service.create_company_with_admin(
                company_name="Company B",
                first_name="Admin",
                last_name="B",
                email="admin-b@test.com",
                password="password123"
            )
        )

        employee_b = user_service.create_employee(
            company_id=company_b.id,
            first_name="Employee",
            last_name="B",
            email="employee-b@test.com",
            password="password123",
            role=EMPLOYEE_CREW
        )

        # Store primitive IDs before leaving this database session.
        company_b_id = company_b.id
        employee_b_id = employee_b.id

    client.post(
        "/login",
        data={
            "email": "admin-a@test.com",
            "password": "password123"
        }
    )

    response = client.post(
        f"/admin/employees/{employee_b_id}/delete"
    )

    # Company A must not be able to access Company B's employee.
    assert response.status_code == 404

    with app.app_context():

        employee_still_exists = (
            user_service.get_company_employee(
                company_id=company_b_id,
                employee_id=employee_b_id
            )
        )

        assert employee_still_exists is not None