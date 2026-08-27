from flask import Flask
from models import db, Company

app = Flask(__name__)

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'

# Connect the database object to Flask app
db.init_app(app)

# Home route for application testing
@app.route('/')
def home():
    return 'RepRequest is running!'

# Create database tables TEST
with app.app_context():
    db.create_all()

    # Test company
    if Company.query.count() == 0:
        test_company = Company(name='Test Company')

        db.session.add(test_company)
        db.session.commit()

        print("Test company created.")

# Runs development server
if __name__ == '__main__':
    app.run(debug=True)