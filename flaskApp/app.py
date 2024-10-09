from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from database import db,create_database
import sqlite3 


app = Flask(__name__)
bootstrap = Bootstrap(app)


##Creates database and configure the app
engine = create_engine("sqlite:///CS2990_Final_Project.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///HeardAndUnderstood.db'
db.init_app(app)
with app.app_context():
    create_database(app)
db=SQLAlchemy(app)




@app.route("/")
def home():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    # email = request.form.get('email')
    # password = request.form.get('password')
    return redirect(url_for('homepage'))


@app.route("/homepage")
def homepage():
    return render_template('home.html')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)
