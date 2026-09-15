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

from app.extensions import db
from models import User


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
    Create a new employee account under the authenticated
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

    if role not in User.EMPLOYEE_ROLES:
        return render_template(
            "admin/create_employee.html",
            error="Invalid employee role."
        )

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        return render_template(
            "admin/create_employee.html",
            error="An employee with that email already exists."
        )

    # SECURITY:
    # Never accept company_id from form input.
    # The new employee must inherit the authenticated
    # administrator's company.
    employee = User(
        company_id=current_user.company_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=role
    )

    employee.set_password(password)

    db.session.add(employee)
    db.session.commit()

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
@role_required(User.ROLE_COMPANY_ADMIN)
def edit_employee(employee_id):
    """
    Edit an employee belonging to the authenticated
    administrator's company.
    """

    # The company_id condition prevents one company's
    # administrator from accessing another company's employee.
    employee = User.query.filter(
        User.id == employee_id,
        User.company_id == current_user.company_id,
        User.role.in_(User.EMPLOYEE_ROLES)
    ).first_or_404()

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

    if role not in User.EMPLOYEE_ROLES:
        return render_template(
            "admin/edit_employee.html",
            employee=employee,
            error="Invalid employee role."
        )

    existing_user = User.query.filter(
        User.email == email,
        User.id != employee.id
    ).first()

    if existing_user:
        return render_template(
            "admin/edit_employee.html",
            employee=employee,
            error="An account with that email already exists."
        )

    employee.first_name = first_name
    employee.last_name = last_name
    employee.email = email
    employee.role = role

    db.session.commit()

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

    employee = User.query.filter(
        User.id == employee_id,
        User.company_id == current_user.company_id,
        User.role.in_(User.EMPLOYEE_ROLES)
    ).first_or_404()

    employee_name = (
        f"{employee.first_name} "
        f"{employee.last_name}"
    )

    db.session.delete(employee)
    db.session.commit()

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