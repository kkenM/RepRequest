from flask import Flask, render_template, request
from models import db, Company, User

app = Flask(__name__)


# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'


# Connect the database object to Flask app
db.init_app(app)


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


# Create database tables
with app.app_context():
    db.create_all()


# Runs development server
if __name__ == '__main__':
    app.run(debug=True)