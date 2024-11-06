from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, json
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from firebase.config import Config
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from database import db,create_database,User,Projects,Involvement,groundTruthing
import sqlite3 
import secrets
import datetime


app = Flask(__name__)
app.config.from_object(Config)


with open('firebase/serviceAccountKey.json') as f:
    service_account = json.load(f)
    app.secret_key = service_account.get("secret_key")


def initialize_firebase():
    cred = credentials.Certificate('firebase/serviceAccountKey.json')
    firebase_admin.initialize_app(cred)


initialize_firebase()
db = firestore.client()


@app.route("/")
def home():
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())

        try:
            # Check if a user with this email already exists
            user_ref = db.collection('users').document(email)
            if user_ref.get().exists:
                flash("An account with this email already exists.", "danger")
                return redirect(url_for('register'))

            user_ref.set({
                'email': email,
                'password': hashed_password.decode('utf-8')
            })
            return redirect(url_for('homepage'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('register'))


@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if request.method == 'POST':
        try:
            # Retrieve user data from Firestore
            user_ref = db.collection('users').document(email)
            user_doc = user_ref.get()

            if user_doc.exists:
                stored_hashed_password = user_doc.to_dict().get('password')

                # Check if the password matches
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                    return redirect(url_for('homepage'))
                else:
                    flash("Invalid password", "danger")
                    return redirect(url_for('login'))
            else:
                flash("User not found", "danger")
                return redirect(url_for('login'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('login'))
    if request.method == "GET":
        return render_template('login.html')

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/homepage")
def homepage():
    return render_template('home.html')

#-----------------PI View-----------------------#
@app.route("/viewAllProjects", methods=['POST', 'GET'])
def viewAllProjects():
    if request.method=='POST':
        searchedName=request.form["s_Name"]
        searched_project=Projects.query.filter(Projects.projectName==searchedName)
        return render_template('viewAllProjects.html',all_project=searched_project)

    else: 
        all_project=Projects.query.all()
        return render_template('viewAllProjects.html',all_project=all_project)


@app.route("/viewAllUsers",methods=['POST', 'GET'])
def viewAllUsers():
    if request.method=='POST':
        searchedName=request.form["s_Name"]
        searched_user=User.query.filter(User.username==searchedName)
        return render_template('viewAllUsers.html',all_users=searched_user)
    else:
        all_users=User.query.all()
        return render_template('viewAllUsers.html',all_users=all_users)


@app.route("/generateNewProject", methods=['POST', 'GET'])
def generateNewProject():
    if request.method=='POST':
        pName=request.form["p_Name"]
        accessCode=secrets.token_hex(3)
        db.session.add(Projects(projectName=pName,projectCode=accessCode,piCreator="JaneDoe1@exmaple.com"))
        db.session.commit()
        return redirect(url_for('generateNewProject'))

    else:
        return render_template('newProject.html')

@app.route("/generateNewCode/<projectName>")
def generateNewCode(projectName):
    newCode=secrets.token_hex(3)
    project=Projects.query.filter(Projects.projectName==projectName).first()
    project.projectCode=newCode
    db.session.commit()
    return redirect(url_for('viewAllProjects'))



@app.route("/groundTruthUpdates")
def groundTruthUpdates():
   
    all_groundTruth=groundTruthing.query.all()
    return render_template('groundTruthingRecords.html',all_groundTruth=all_groundTruth)

def testData():
    
    db.session.add_all([
    User(email='JaneDoe1@example.com', username='JaneDoe', password='password1', status=1),
    User(email='JoeDoe@example.com', username='JohnDoe', password='password2', status=0),
   
   ]
)
    db.session.commit()

    # Create Projects
    db.session.add_all([
    Projects(projectName="Project1",projectCode='1234', piCreator='JaneDoe1@example.com'),
    Projects(projectName="Project2",projectCode='4321', piCreator='JaneDoe1@example.com')]
    )

   
    db.session.commit()  

    # # Create Involvements
    db.session.add_all([
        Involvement(id=1,user_id="JaneDoe1@example.com", project_id="Project1"),
        Involvement(id=2,user_id="JaneDoe1@example.com", project_id="Project1"),
        Involvement(id=3,user_id="JaneDoe1@example.com", project_id="Project2")
    ])
    
   
   
    db.session.commit()  

   







if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)

