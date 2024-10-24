from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from database import db,create_database,User,Projects,Involvement
import sqlite3 


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


@app.route("/homepage")
def homepage():
    return render_template('home.html')

#-----------------PI View-----------------------#
@app.route("/viewAllProjects")
def viewAllProjects():
    testData()
    all_project=Projects.query.all()

    return render_template('viewAllProjects.html',all_project=all_project)


@app.route("/viewAllUsers")
def viewAllUsers():

    return render_template()


@app.route("/generateNewProjectCode")
def generateNewProjectCode():

    return render_template()


@app.route("/groudTruthUpdates")
def groudTruthUpdates():

    return render_template()

def testData():
    
#     db.session.add_all([
#     User(email='JaneDoe1@example.com', username='JaneDoe', password='password1', status=1),
#     User(email='JoeDoe@example.com', username='JohnDoe', password='password2', status=0),
   
#    ]
# )
#     db.session.commit()

#     # Create Projects
#     db.session.add_all([
#     Projects(projectName="Project1",projectCode='1234', piCreator='JaneDoe1@example.com'),
#     Projects(projectName="Project2",projectCode='4321', piCreator='JaneDoe1@example.com')]
#     )

   
#     db.session.commit()  

    # # # Create Involvements
    # db.session.add_all([
    #     Involvement(id=1,user_id="JaneDoe1@example.com", project_id="Project1"),
    #     Involvement(id=2,user_id="JaneDoe1@example.com", project_id="Project1"),
    #     Involvement(id=3,user_id="JaneDoe1@example.com", project_id="Project2")
    # ])
    
   
   
    db.session.commit()  

   





if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)

