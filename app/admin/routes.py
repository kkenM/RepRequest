"""
Company administration routes for RepRequest.

Responsibilities:
- Display employees belonging to the current company
- Create employee accounts
- Edit employee accounts
- Delete employee accounts
- Protect administrative functionality by user role

IMPORTANT:
All employee operations must be scoped to the authenticated
administrator's company_id.
"""

from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

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


def role_required(*allowed_roles):
    """
    Restrict a route to authenticated users whose role
    appears in allowed_roles.

    This decorator will be moved into a reusable authorization
    module during a later refactoring step.
    """

    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):

            if current_user.role not in allowed_roles:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


@admin_bp.route("/", strict_slashes=False)
@role_required(User.ROLE_COMPANY_ADMIN)
def dashboard():
    """
    Display employees belonging to the authenticated
    administrator's company.
    """

    employees = User.query.filter(
        User.company_id == current_user.company_id,
        User.role.in_(User.EMPLOYEE_ROLES)
    ).order_by(
        User.last_name,
        User.first_name
    ).all()

    return render_template(
        "admin/admin.html",
        employees=employees
    )


@admin_bp.route(
    "/employees/create",
    methods=["GET", "POST"]
)
@role_required(User.ROLE_COMPANY_ADMIN)
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
@role_required(User.ROLE_COMPANY_ADMIN)
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
@role_required(User.ROLE_COMPANY_ADMIN)
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


@admin_bp.app_errorhandler(403)
def forbidden(error):
    """
    Display a friendly page when access is denied.
    """

    return render_template(
        "errors/403.html"
    ), 403