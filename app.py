import os

from flask import Flask, render_template, request, redirect, url_for
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
        role="company-admin"
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


# Create database tables
with app.app_context():
    db.create_all()


# Runs development server
if __name__ == '__main__':
    app.run(debug=True)