from flask import Flask
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

# Updates existing database with new implementations
# Justin (I didnt copy and paste all the discord code)
with app.app_context():

    # ==================================================
    # RESET DATABASE
    # ==================================================

    # Delete all existing tables/data
    db.drop_all()

    # Recreate all tables
    db.create_all()

    print("Database reset successfully.")

    # ==================================================
    # CREATE TEST COMPANY
    # ==================================================

    test_company = Company(
        name="Rocky Mountain Fabrication"
    )

    db.session.add(test_company)
    db.session.commit()

    print("Test company created.")

    # ==================================================
    # CREATE TEST USERS
    # ==================================================

    admin_user = User(
        company_id=test_company.id,
        first_name="Jim",
        last_name="Bob",
        email="jim.bob@rockymountainfab.com",
        password_hash="temp",
        role="company-admin"
    )

    employee_user = User(
        company_id=test_company.id,
        first_name="Sarah",
        last_name="Smith",
        email="sarah.smith@rockymountainfab.com",
        password_hash="temp",
        role="employee"
    )

    technician_user = User(
        company_id=test_company.id,
        first_name="Mike",
        last_name="Johnson",
        email="mike.johnson@rockymountainfab.com",
        password_hash="temp",
        role="technician"
    )

    db.session.add_all([
        admin_user,
        employee_user,
        technician_user
    ])

    db.session.commit()

    print("Test users created.")

    # ==================================================
    # DISPLAY COMPANY
    # ==================================================

    companies = Company.query.all()

    print("\n========================================")
    print("COMPANIES IN DATABASE")
    print("========================================")

    for company in companies:
        print("\nCOMPANY")
        print("----------------------------------------")
        print(f"Company ID:      {company.id}")
        print(f"Company Name:    {company.name}")
        print(f"Created At:      {company.created_at}")

    # ==================================================
    # DISPLAY USERS
    # ==================================================

    users = User.query.all()

    print("\n========================================")
    print("USERS IN DATABASE")
    print("========================================")

    for user in users:
        print("\nUSER")
        print("----------------------------------------")
        print(f"User ID:         {user.id}")
        print(f"Company ID:      {user.company_id}")
        print(f"First Name:      {user.first_name}")
        print(f"Last Name:       {user.last_name}")
        print(f"Email:           {user.email}")
        print(f"Password Hash:   {user.password_hash}")
        print(f"Role:            {user.role}")
        print(f"Created At:      {user.created_at}")

        # Test the SQLAlchemy relationship
        print(
            f"Relationship:    {user.first_name} {user.last_name} "
            f"belongs to {user.company.name}"
        )

    # ==================================================
    # TEST SUMMARY
    # ==================================================

    print("\n========================================")
    print("DATABASE TEST SUMMARY")
    print("========================================")
    print(f"Total Companies: {Company.query.count()}")
    print(f"Total Users:     {User.query.count()}")
    print("Database test completed successfully.")


# Runs development server
if __name__ == '__main__':
    app.run(debug=True)