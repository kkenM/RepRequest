"""
Temporary centralized route definitions for RepRequest.

These routes preserve the application's existing behavior while
the application-factory architecture is introduced.

Step B will separate these routes into feature-specific Blueprints:
- main
- auth
- admin
"""

from functools import wraps

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app.extensions import db, login_manager
from models import Company, User


@login_manager.user_loader
def load_user(user_id):
    """
    Reload a logged-in user from the database using the user ID
    stored in the Flask session.
    """

    return db.session.get(User, int(user_id))


def role_required(*allowed_roles):
    """
    Restrict a route to authenticated users whose role is included
    in allowed_roles.
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


def register_routes(app):
    """
    Register RepRequest's current routes with the Flask application.

    This function exists as a transitional design. Step B will
    replace it with Flask Blueprints.
    """

    @app.route("/")
    def home():
        return "RepRequest is running!"


    @app.route("/register", methods=["GET", "POST"])
    def register():

        if request.method == "GET":
            return render_template("register.html")

        company_name = request.form["company_name"].strip()
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if (
            not company_name
            or not first_name
            or not last_name
            or not email
            or not password
        ):
            return render_template(
                "register.html",
                error="All fields are required."
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return render_template(
                "register.html",
                error="An account with that email already exists."
            )

        company = Company(
            name=company_name
        )

        db.session.add(company)
        db.session.flush()

        admin_user = User(
            company_id=company.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=User.ROLE_COMPANY_ADMIN
        )

        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        return redirect(url_for("login"))


    @app.route("/login", methods=["GET", "POST"])
    def login():

        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":

            email = request.form["email"].strip().lower()
            password = request.form["password"]

            user = User.query.filter_by(
                email=email
            ).first()

            if user and user.check_password(password):

                login_user(user)

                return redirect(url_for("dashboard"))

            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        return render_template("login.html")


    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")


    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():

        logout_user()

        return redirect(url_for("login"))


    @app.route("/admin")
    @role_required(User.ROLE_COMPANY_ADMIN)
    def admin():

        # Retrieve employees belonging only to the currently
        # logged-in administrator's company
        employees = User.query.filter(
            User.company_id == current_user.company_id,
            User.role.in_(User.EMPLOYEE_ROLES)
        ).order_by(
            User.last_name,
            User.first_name,
        ).all()

        return render_template(
            "admin.html",
            employees=employees
        )


    @app.route("/admin/employees/create", methods=["GET", "POST"])
    @role_required(User.ROLE_COMPANY_ADMIN)
    def create_employee():

        # Display employee creation form
        if request.method == "GET":
            return render_template("create_employee.html")

        # Get submitted employee information
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]

        # Verify all fields contain a value
        if (
            not first_name
            or not last_name
            or not email
            or not password
            or not role
        ):
            return render_template(
                "create_employee.html",
                error="All fields are required."
            )


        if role not in User.EMPLOYEE_ROLES:
            return render_template(
                "create_employee.html",
                error="Invalid employee role."
            )

        # Make sure email is not already registered
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template(
                "create_employee.html",
                error="An employee with that email already exists."
            )

        # Create employee under the CURRENT ADMIN's company
        employee = User(
            company_id=current_user.company_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )

        # Securely hash temp password
        employee.set_password(password)

        db.session.add(employee)
        db.session.commit()

        flash(
            "Employee account created successfully.",
            "success"
        )

        return redirect(url_for("admin"))

    @app.route("/admin/employees/<int:employee_id>/edit", methods=["GET", "POST"])
    @role_required(User.ROLE_COMPANY_ADMIN)
    def edit_employee(employee_id):
        # Find the employee, but only if they belong
        # to the current administrator's company
        employee = User.query.filter(
            User.id == employee_id,
            User.company_id == current_user.company_id,
            User.role.in_(User.EMPLOYEE_ROLES)
        ).first_or_404()

        # Display edit form
        if request.method == "GET":
            return render_template(
                "edit_employee.html",
                employee=employee
            )

        # Retrieve updated information
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        role = request.form["role"]

        # Validate required fields
        if (
            not first_name
            or not last_name
            or not email
            or not role
        ):
            return render_template(
                "edit_employee.html",
                employee=employee,
                error="All fields are required."
            )

        # Only employee roles are permitted
        if role not in User.EMPLOYEE_ROLES:
            return render_template(
                "edit_employee.html",
                employee=employee,
                error="Invalid employee role."
            )

        # Check whether another user already has this email
        existing_user = User.query.filter(
            User.email == email,
            User.id != employee.id
        ).first()

        if existing_user:
            return render_template(
                "edit_employee.html",
                employee=employee,
                error="An account with that email already exists."
            )

        # Update employee information
        employee.first_name = first_name
        employee.last_name = last_name
        employee.email = email
        employee.role = role

        db.session.commit()

        flash(
            "Employee account updated successfully.",
            "success"
        )

        return redirect(url_for("admin"))


    @app.route("/admin/employees/<int:employee_id>/delete", methods=["POST"])
    @role_required(User.ROLE_COMPANY_ADMIN)
    def delete_employee(employee_id):

        # Only retrieve employees belonging to
        # the current administrator's company
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

        return redirect(url_for("admin"))


    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403