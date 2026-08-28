from flask import Flask
from models import db

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
with app.app_context():
    db.create_all()

# Runs development server
if __name__ == '__main__':
    app.run(debug=True)