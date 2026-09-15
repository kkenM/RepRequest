import os

from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    flash
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from models import db, Company, User

app = Flask(__name__)

# Secret key used to protect Flask sessions
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key-change-before-production"
)

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'


# Connect the database object to Flask app
db.init_app(app)


# Configure user login management
login_manager = LoginManager()
login_manager.init_app(app)

# Send unauthenticated users to the login page
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def role_required(*allowed_roles):
    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):

            # Check if the current user's role is allowed
            if current_user.role not in allowed_roles:
                abort(403)

            return view_function(*args, **kwargs)
        return wrapped_view
    return decorator

# Home route for application testing
@app.route('/')
def home():
    return 'RepRequest is running!'


# Company registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    # Display the registration page
    if request.method == "GET":
        return render_template("register.html")

    # Get submitted form information
    company_name = request.form["company_name"].strip()
    first_name = request.form["first_name"].strip()
    last_name = request.form["last_name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]

    if not company_name or not first_name or not last_name or not email or not password:
        return render_template(
            "register.html",
            error="All fields are required."
        )

    # Check whether the email is already registered
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return render_template(
            "register.html",
            error="An account with that email already exists."
        )

    # Create the company
    company = Company(
        name=company_name
    )

    db.session.add(company)

    # Save company first so SQLAlchemy generates its ID
    db.session.flush()

    # Create the company's first administrator
    admin_user = User(
        company_id=company.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=User.ROLE_COMPANY_ADMIN
    )

    # Hash the password before storing it
    admin_user.set_password(password)

    db.session.add(admin_user)

    # Save both records
    db.session.commit()

    return (
        f"Company '{company.name}' registered successfully. "
        f"{admin_user.first_name} {admin_user.last_name} "
        f"is the company administrator."
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    # If the user is already logged in,
    # send them directly to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    # Process submitted login information
    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Search for an account using this email
        user = User.query.filter_by(email=email).first()

        # Verify that the user exists and the password is correct
        if user and user.check_password(password):

            login_user(user)

            return redirect(url_for("dashboard"))

        # Login failed
        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    # Display login page
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# Logout
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

    return render_template("admin.html", employees=employees)


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
    password = request.form["password"].strip()
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

@app.route(
    "/admin/employees/<int:employee_id>/delete",
    methods=["POST"]
)
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

# Create database tables
with app.app_context():
    db.create_all()


# Runs development server
if __name__ == '__main__':
    app.run(debug=True)