"""
Company-administration HTTP routes.

Routes should read requests, perform request-level validation,
call service-layer operations, and return responses.

Database and business operations should live in app.services rather
than being implemented directly in this module.
"""

# Test

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import current_user

from app.roles import EMPLOYEE_ROLE_OPTIONS
from app.authorization import company_admin_required
from app.models import User
from app.services import user_service
from app.services.exceptions import (
    DuplicateEmailError,
    InvalidEmployeeRoleError
)


# All routes in this Blueprint begin with /admin
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

@admin_bp.context_processor
def inject_employee_role_options():
    """
    Make valid employee role choices available to all
    templates rendered by the admin Blueprint.
    """

    return {
        "employee_role_options": EMPLOYEE_ROLE_OPTIONS
    }


@admin_bp.route("/", strict_slashes=False)
@company_admin_required
def dashboard():
    """
    Display employees belonging to the authenticated
    administrator's company.
    """

    employees = user_service.get_company_employees(
        current_user.company_id
    )

    return render_template(
        "admin/admin.html",
        employees=employees
    )


@admin_bp.route(
    "/employees/create",
    methods=["GET", "POST"]
)
@company_admin_required
def create_employee():
    """
    Create an employee belonging to the authenticated
    administrator's company.
    """

    if request.method == "GET":
        return render_template(
            "admin/create_employee.html"
        )

    first_name = request.form["first_name"].strip()
    last_name = request.form["last_name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]
    role = request.form["role"]

    if (
        not first_name
        or not last_name
        or not email
        or not password
        or not role
    ):
        return render_template(
            "admin/create_employee.html",
            error="All fields are required."
        )

    try:
        user_service.create_employee(
            # SECURITY:
            # The company comes from the authenticated administrator,
            # never from browser-submitted form data.
            company_id=current_user.company_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            role=role
        )

    except InvalidEmployeeRoleError:
        return render_template(
            "admin/create_employee.html",
            error="Invalid employee role."
        )

    except DuplicateEmailError:
        return render_template(
            "admin/create_employee.html",
            error="An account with that email already exists."
        )

    flash(
        "Employee account created successfully.",
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )

@admin_bp.route(
    "/employees/<int:employee_id>/edit",
    methods=["GET", "POST"]
)
@admin_bp.route(
    "/employees/<int:employee_id>/edit",
    methods=["GET", "POST"]
)
@company_admin_required
def edit_employee(employee_id):
    """
    Edit an employee belonging to the authenticated
    administrator's company.
    """

    employee = user_service.get_company_employee(
        company_id=current_user.company_id,
        employee_id=employee_id
    )

    # Return 404 instead of exposing employees belonging
    # to another company.
    if employee is None:
        abort(404)

    if request.method == "GET":
        return render_template(
            "admin/edit_employee.html",
            employee=employee
        )

    first_name = request.form["first_name"].strip()
    last_name = request.form["last_name"].strip()
    email = request.form["email"].strip().lower()
    role = request.form["role"]

    if (
        not first_name
        or not last_name
        or not email
        or not role
    ):
        return render_template(
            "admin/edit_employee.html",
            employee=employee,
            error="All fields are required."
        )

    try:
        user_service.update_employee(
            employee=employee,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )

    except InvalidEmployeeRoleError:
        return render_template(
            "admin/edit_employee.html",
            employee=employee,
            error="Invalid employee role."
        )

    except DuplicateEmailError:
        return render_template(
            "admin/edit_employee.html",
            employee=employee,
            error="An account with that email already exists."
        )

    flash(
        "Employee account updated successfully.",
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )


@admin_bp.route(
    "/employees/<int:employee_id>/delete",
    methods=["POST"]
)
@company_admin_required
def delete_employee(employee_id):
    """
    Delete an employee belonging to the authenticated
    administrator's company.
    """

    employee = user_service.get_company_employee(
        company_id=current_user.company_id,
        employee_id=employee_id
    )

    if employee is None:
        abort(404)

    employee_name = (
        f"{employee.first_name} "
        f"{employee.last_name}"
    )

    user_service.delete_employee(
        employee
    )

    flash(
        f"{employee_name} was deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )