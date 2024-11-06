from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from database import db,create_database,User,Projects,Involvement,groundTruthing
import sqlite3 
import secrets
import datetime


app = Flask(__name__)
bootstrap = Bootstrap(app)


##Creates database and configure the app
engine = create_engine("sqlite:///CS2990_Final_Project.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///HeardAndUnderstood.db'
db.init_app(app)


with app.app_context():
    create_database(app)


@app.route("/")
def home():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    # email = request.form.get('email')
    # password = request.form.get('password')
    return redirect(url_for('homepage'))

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

