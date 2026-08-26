from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'

# Connect SQLAlchemy to Flask
database = SQLAlchemy(app)

@app.route('/')
def home():
    return 'RepRequest is running!'

if __name__ == '__main__':
    app.run(debug=True)