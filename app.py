from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, json
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt, secrets
from firebase.config import Config
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from database import db,create_database,User,Projects,Involvement,groundTruthing
import sqlite3 
import secrets
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter

from db_utils import upload_file_to_db, connect_to_database
from flask_mail import Mail, Message
#import email_credentials
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.config.from_object(Config)
Bootstrap(app)

##Information from logged in user
statusFlag="User"
StatusEmail=""


##Firebase Connection
with open('firebase/serviceAccountKey.json') as f:
    service_account = json.load(f)
    app.secret_key = service_account.get("secret_key")


def initialize_firebase():
    cred = credentials.Certificate('firebase/serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

initialize_firebase()
db = firestore.client()
######################


# Configure Flask-Mail email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP email server 
app.config['MAIL_PORT'] = 587
#app.config['MAIL_USERNAME'] = email_credentials.hua_email
#app.config['MAIL_PASSWORD'] = email_credentials.hua_password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


###Login/Register Pages################################################
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
        Institute=request.form.get('Institute')
        name=request.form.get('name')

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
                'password': hashed_password.decode('utf-8'),
                'status':'User',
                'name':name,
                'Institute':Institute,
                'projects':[]
            })

            global StatusEmail
            StatusEmail=email
            return redirect(url_for('homepage', email=email))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('register'))

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/pi_access_request', methods=['GET', 'POST'])
def pi_access_request():
    name = request.form.get('name')
    email = request.form.get('email')
    institution = request.form.get('institution')
    if request.method == 'POST':
        try:
            # Add request to HUA firebase
            requests_ref = db.collection('request')
            requests_doc = requests_ref.add({"username":email})

            # Send email
           # recipients = email_credentials.recipients

           # emailMessage = Message("Request for PI Access", sender=email,recipients=recipients)
            #emailMessage.body = f"Hello Bob and Donna,\n\n {name} is requesting admin access. {name} is from {institution} and reachable at {email}.\n\n You will find their request on the View Requests for Access page in the Heard and Understood App."
            #mail.send(emailMessage)
            print('email sent successfully!')
        except Exception as e:
            print('problem sending email')
            print(e)

        return redirect(url_for('homepage'))
    return render_template('pi_access_request.html')

@app.route('/pre_approved_access_code', methods=['GET', 'POST'])
def pre_approved_access_code():
    access_code = request.form.get('PIAccessCode')
    if request.method == 'POST':
        try:
            print(f"pre-approved code {access_code} entered")
        except:
            print("issue with pre-approved code")
        return redirect(url_for('homepage'))
    return render_template('pre_approved_access_code.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        user_ref = db.collection('users').document(email)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            verification_secret = secrets.token_hex(3)
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=15)

            
            user_ref.update({
                'verification_code': verification_secret,
                'verification_expiry': expiration_time
            })
            
            subject = "HUA Password Reset"
            body = f"""Hi,

You recently requested a password reset for HUA. Your verification code is below.

{verification_secret}

This code will expire in 15 minutes.

If you didn't request a password reset, you can safely disregard this email.

This account is not monitored, please do not reply to this email.
"""
            try:
                msg = Message(subject, sender="Huaverso@gmail.com", recipients=[email], body=body)
                mail.send(msg)
                
                flash("A verification code has been sent to your email.", "success")
                return redirect(url_for('enter_code', email=email))
            except Exception:
                flash("Failed to send verification email. Please try again later.", "danger")
                return redirect(url_for('reset_password'))
        else:
            flash("No account with this email exists.", "danger")
            return redirect(url_for('reset_password'))
    
    return render_template('reset_password.html')

@app.route('/enter_code', methods=['GET', 'POST'])
def enter_code():
    email = request.args.get('email')
    if not email:
        flash("Invalid request.", "danger")
        return redirect(url_for('reset_password'))
    
    if request.method == 'POST':
        entered_code = request.form.get('verification_code').strip()
        user_ref = db.collection('users').document(email)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            flash("Invalid request.", "danger")
            return redirect(url_for('reset_password'))
        
        stored_code = user_doc.to_dict().get('verification_code')
        expiry_time = user_doc.to_dict().get('verification_expiry')
        
        if not stored_code or not expiry_time:
            flash("No verification code found. Please initiate the password reset again.", "danger")
            return redirect(url_for('reset_password'))

        if entered_code != stored_code:
            flash("Invalid verification code.", "danger")
            return redirect(url_for('enter_code', email=email))
        
        if datetime.now(timezone.utc) > expiry_time:
            flash("The verification code has expired. Please request a new one.", "danger")
            user_ref.update({
                'verification_code': firestore.DELETE_FIELD,
                'verification_expiry': firestore.DELETE_FIELD
            })
            return redirect(url_for('reset_password'))
        
        return redirect(url_for('new_password', email=email))
    
    return render_template('enter_code.html', email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("Form Data:", request.form)
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            # Retrieve user data from Firestore
            user_ref = db.collection('users').document(email)
            user_doc = user_ref.get()

            if user_doc.exists:
                stored_hashed_password = user_doc.to_dict().get('password')

                # Ensure the stored hashed password exists
                if stored_hashed_password:
                    # Encode the stored hashed password to bytes
                    stored_hashed_password_bytes = stored_hashed_password.encode('utf-8')

               

                # Check if the password matches
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                    global statusFlag 
                    statusFlag = user_doc.to_dict().get('status')
                    global StatusEmail
                    StatusEmail=email
                    return redirect(url_for('homepage', email=email))
                else:
                    flash("Invalid password", "danger")
                    return redirect(url_for('login'))
            else:
                flash("User not found", "danger")
                return redirect(url_for('login'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('login'))
    
    # Handle GET requests
    return render_template('login.html')
############################################################################

##############Dashboard###########
@app.route("/homepage")
def homepage():
    global StatusEmail
    user_Ref=db.collection("users").document(StatusEmail)
    user_Coll=user_Ref.get()
    project_Coll=user_Coll.get("projects")
   
    if statusFlag=="Admin":
        return render_template('AdminView/homeAdmin.html',projects=project_Coll)
    elif statusFlag=="PI":
        return render_template('PIView/homePI.html',projects=project_Coll)
    else:
            return render_template('UserView/homeUser.html',projects=project_Coll)

@app.route('/new_password', methods=['GET', 'POST'])
def new_password():
    email = request.args.get('email')
    if not email:
        flash("Invalid request.", "danger")
        return redirect(url_for('reset_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('new_password', email=email))
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for('new_password', email=email))
        
        # Hash the new password and decode to store as string
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_ref = db.collection('users').document(email)
        user_ref.update({'password': hashed_password})
        
        user_ref.update({
            'verification_code': firestore.DELETE_FIELD,
            'verification_expiry': firestore.DELETE_FIELD
        })
        
        flash("Your password has been successfully reset. You can now log in.", "success")
        return redirect(url_for('home'))
    
    return render_template('new_password.html', email=email)

@app.route('/logout')
def logout():
    return url_for('login')


@app.route('/contact')
def contact():
    return render_template('PIView/contact-admin.html')

@app.route("/profile", methods=["POST", "GET"])
def profile():
    global StatusEmail
    if statusFlag=="User":
        return render_template("UserView/UserProfile.html",email=StatusEmail)
    elif statusFlag=="PI":
        return render_template("PIView/PIProfile.html",email=StatusEmail)
    else:
        return render_template("AdminView/AdminProfile.html",email=StatusEmail)

@app.route("/change-profile", methods=['GET', 'POST'])
def change_profile():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
       
    if statusFlag=="User":
        return render_template("UserView/change-profile.html",email=StatusEmail)
    elif statusFlag=="PI":
        return render_template("PIView/change-profile.html",email=StatusEmail)
    else:
        return render_template("AdminView/change-profile.html",email=StatusEmail)

 


#############################


###################################Project views######################

@app.route("/dashboard")
def dashboard():
    if(statusFlag=="User"):
        return render_template("UserView/dashboardUser.html")
        
    elif(statusFlag=="PI"):
        return render_template("PIView/dashboardPI.html")
    else:
        return render_template("AdminView/dashboardAdmin.html")
    
@app.route("/ground_truthing")
def ground_truthing():
    return render_template("ground_truthing.html")

@app.route("/import")
def upload():
    if (statusFlag=="User"):
        return render_template('UserView/importPageUser.html')
    elif(statusFlag=="PI"):
        return render_template('PIView/importPagePI.html')
    else:
        return render_template('AdminView/importPageAdmin.html')

@app.route("/upload_file", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400
    if file:
        file_data = file.read()
        file_name = file.filename
        file_type = file.content_type
        success = upload_file_to_db(file_name, file_type, file_data)
        if success:
            return redirect(url_for('upload'))
        else:
            return "Failed to upload", 500

@app.route("/view-files")
def view_files():
    connection = connect_to_database()
    if connection is None:
        return "Database connection failed", 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("select id, file_name, file_type from audio_files")
        files = cursor.fetchall()
        return render_template('view-files.html', files=files)
    finally:
        cursor.close()
        connection.close()




#-----------------PI View-----------------------#

##Allows PI to see every project
@app.route("/viewAllProjectsPI", methods=['POST', 'GET'])
def viewAllProjectsPI():

    if request.method=='POST':
       
       
        ##Project name being searched
        searchedName=request.form["s_Name"]
        
        searched_projects=[]

        project_ref = (db.collection("PI").document("fdeolive@uvm.edu").collection("project"))
        query_ref=project_ref.where(filter=FieldFilter("project_name", "==",searchedName)).stream()

        for doc in  query_ref:
         searched_projects.append(doc.to_dict())
        return render_template('PIView/viewAllProjectsPI.html',all_project=searched_projects)
    
    else: 

        all_project_ref=db.collection("PI").document("fdeolive@uvm.edu").collection("project")
        all_project_coll=all_project_ref.get()
        all_projects=[]

        for doc in all_project_coll:
            project = doc.to_dict()  
            all_projects.append(project)
    
        return render_template('PIView/viewAllProjectsPI.html',all_project=all_projects)
       

# @app.route("/viewAllUsersPI",methods=['POST', 'GET'])
# def viewAllUsersPI():
#     if request.method=='POST':
#         searchedName=request.form["s_Name"]
#         searched_users=[]
        
#         piProjects=db.collection("users").document("PI_username@uvm.edu")
#         piProjectsColl=piProjects.get()
#         all_users=[]
#         piProjectsCollProject=piProjectsColl.get('projects')
#         if(piProjectsCollProject==0):
#             all_users=["No members"]
#         else:
#                 docs=db.collection("users").where(filter=FieldFilter("projects", "array_contains_any",piProjectsCollProject)).where(filter=FieldFilter("email", "in",searchedName)).stream()
#                 for doc in docs:
#                     users=doc.to_dict()
#                     searchedName.append(users)


#         return render_template('PIView/viewAllUsersPI.html',all_users=searched_users)


#     else: 
#         piProjects=db.collection("users").document("PI_username@uvm.edu")
#         piProjectsColl=piProjects.get()
#         all_users=[]
#         piProjectsCollProject=piProjectsColl.get('projects')
#         if(piProjectsCollProject==0):
#             all_users=["No members"]
#         else:
#                 docs=db.collection("users").where(filter=FieldFilter("projects", "array_contains_any",piProjectsCollProject)).stream()
#                 for doc in docs:
#                     users=doc.to_dict()
#                     all_users.append(users)
               
#         return render_template('PIView/viewAllUsersPI.html',all_users=all_users)

###Creates a new project:
###Creates new project in firebase project's collection
##Inserts into project array within users collection
@app.route("/generateNewProject", methods=['POST', 'GET'])
def generateNewProject():
    if request.method=='POST':
        pName=request.form["p_Name"]
        accessCode=secrets.token_hex(3)
        

        global StatusEmail
        ###Updates projects in user
        user_ref = db.collection("users").document(StatusEmail)
        user_ref.update({"projects": firestore.ArrayUnion([pName])})

        ##Updates project collection
        project_ref = db.collection("projects").document(pName)
        project_ref.set({"access_code":accessCode,'project_name':pName,"projectMembers":[],"PI_email":StatusEmail})

        
        return redirect(url_for('generateNewProject'))

    else:
        if (statusFlag=="PI"):
            return render_template('PIView/newProjectPI.html')
        else :
            return render_template('AdminView/newProjectAdmin.html')


##Project Name has to be unqiue **Potentially a problem
@app.route("/generateNewCode/<projectName>")
def generateNewCode(projectName):

    newCode=secrets.token_hex(3)
    global StatusEmail
    projectRef=db.collection("projects").document(projectName)
    
    projectRef.update({'access_code':newCode})
    if(statusFlag=="PI"):
        return redirect(url_for('PIView/viewAllProjectsPI'))
    else:
        return redirect(url_for('AdminView/viewAllProjectsAdmin'))



@app.route("/groundTruthUpdates")
def groundTruthUpdates():
    groundTruthing_ref=db.collection("groundTruthing")
    groundTruthing_records=[]
    global StatusEmail
    query_ref=groundTruthing_ref.where(filter=FieldFilter("PI_email", "==",StatusEmail)).stream()
    for doc in  query_ref:
         groundTruthing_records.append(doc.to_dict())

    
    
    if (statusFlag=="PI"):  
        return render_template('PIView/groundTruthingRecordsPI.html',all_groundTruth=groundTruthing_records)
    
    else:
        return render_template('AdminView/groundTruthingRecordsAdmin.html',all_groundTruth=groundTruthing_records)
   
    

#-Super PI-#

@app.route('/registerNewPI', methods=['GET', 'POST'])
def registerNewPI():
    if request.method == 'GET':
        return render_template('AdminView/registerNewPi.html')
    else:
        email = request.form.get('email')
        Institute = request.form.get('Institute')
        name = request.form.get('name')
       
        password = secrets.token_hex(3)

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())

        try:
            # Check if a user with this email already exists
            user_ref = db.collection('users').document(email)
            if user_ref.get().exists:
                flash("An account with this email already exists.", "danger")
                return redirect(url_for('registerNewPI'))

            user_ref.set({
                 'email': email,
                'password': hashed_password.decode('utf-8'),
                'status':'PI',
                'name':name,
                'Institute':Institute,
                'projects':[]
            })

         

            return redirect(url_for('registerNewPI'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('registerNewPI'))


@app.route('/piRequest', methods=['GET','POST'])
def piRequest():
   
    all_request_ref=db.collection("request")
    all_request_coll=all_request_ref.get()

    all_request=[]
    for doc in all_request_coll:
        requests = doc.to_dict()  
        all_request.append(requests)

    return render_template('AdminView/piRequest.html', all_request=all_request)

@app.route("/acceptRequest/<pName>")
def acceptRequest(pName):
    users_ref = (
    db.collection("users").document(pName))
    users_ref.update({'status':'PI'})

    db.collection("request").document(pName).delete()
    return redirect(url_for('piRequest'))

@app.route("/declineRequest/<pName>")
def declineRequest(pName):
   
    db.collection("request").document(pName).delete()
    
    return redirect(url_for('piRequest'))


@app.route("/viewAllProjectsAdmin", methods=['POST', 'GET'])
def viewAllProjectsAdmin():

    global StatusEmail
    project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",StatusEmail))

    if request.method=='POST':
       
       
        ##Project name being searched
        searchedName=request.form["s_Name"]
        
        searched_projects=[]
        
      
        query_ref=project_ref.where(filter=FieldFilter("project_name", "==",searchedName)).stream()

        for doc in  query_ref:
         searched_projects.append(doc.to_dict())
        return render_template('AdminView/viewAllProjectsAdmin.html',all_project=searched_projects)
    
    else: 
       
        all_project_coll=project_ref.get()
        all_projects=[]

        for doc in all_project_coll:
            project = doc.to_dict()  
            all_projects.append(project)
    
        return render_template('AdminView/viewAllProjectsAdmin.html',all_project=all_projects)


@app.route("/viewAllUsersAdmin",methods=['POST', 'GET'])
def viewAllUsersAdmin():
    if request.method=='POST':
        searchedName=request.form["s_Name"]
        searched_users=[]
        
        docs_ref = (
        db.collection("users").document(searchedName))
        doc=docs_ref.get()

        foundUser = doc.to_dict()  
        searched_users.append(foundUser)


        return render_template('AdminView/viewAllUsersAdmin.html',all_users=searched_users)


    else: 
        all_users_ref=db.collection("users")
        all_users_coll=all_users_ref.get()

        all_users=[]
        for doc in all_users_coll:
            usersDic = doc.to_dict()  
            all_users.append(usersDic)

        print(all_users)

        return render_template('AdminView/viewAllUsersAdmin.html',all_users=all_users)



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)

