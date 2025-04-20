# from flask import Flask, render_template, request, redirect, url_for, flash, json,session
# from flask_session import Session
# import firebase_admin
# from firebase_admin import credentials, firestore
# import bcrypt, secrets
# from firebase.config import Config
# from flask_bootstrap import Bootstrap
# import secrets
# import datetime
# from google.cloud.firestore_v1.base_query import FieldFilter
# from db_utils import upload_file_to_db, connect_to_database
# from flask_mail import Mail, Message
# from datetime import datetime, timedelta, timezone
# import uuid
#########
from flask import Flask, render_template, request, redirect, url_for, flash, json, jsonify, send_from_directory,session
from flask_session import Session
import firebase_admin
from flask_bootstrap import Bootstrap
from firebase_admin import credentials, firestore
import bcrypt, secrets
from google.cloud.firestore_v1.base_query import FieldFilter
from hua.firebase.config import Config
from hua.db_utils import upload_file_to_db, connect_to_database
from hua.consert.consert_process import ConsertProcess
from flask_mail import Mail, Message
import email_credentials as email_credentials
from datetime import datetime, timedelta, timezone
import os
import uuid


##Flash if no project exist with that access code

##App configurations;Bootstrap,Session,and Mail
app = Flask(__name__)
app.config.from_object(Config)
Bootstrap(app)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)  

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP email server 
app.config['MAIL_PORT'] = 587
#app.config['MAIL_USERNAME'] = email_credentials.hua_email
#app.config['MAIL_PASSWORD'] = email_credentials.hua_password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


project_cache=[]
##Firebase Connection
with open('serviceAccountKey.json') as f:
    service_account = json.load(f)
    app.secret_key = service_account.get("secret_key")

def initialize_firebase():
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
initialize_firebase()
db = firestore.client()

###########





##########################Login/Register Pages################################################
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

            ##Creates user in firebase
            user_ref.set({
                'email': email,
                'password': hashed_password.decode('utf-8'),
                'status':'User',
                'name':name,
                'Institute':Institute
            })
            ##Stores users information during their session
            session["user"] = {
                 "name": name,
                 "email": email,
                "status": "User",
                "institute":Institute}
            
            return redirect(url_for('homepage', email=email))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('register'))

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/pi_access_request', methods=['GET', 'POST'])
def pi_access_request():
    user=session.get("user")
    user_email=user.get("email")
    user_name=user.get("name")
    
    if request.method == 'POST':
        try:
            # Add request to HUA firebase
            requests_ref = db.collection('request').document(user_email)
            requests_doc = requests_ref.set({"email":user_email,"name":user_name})

            # Send email
           # recipients = email_credentials.recipients

           # emailMessage = Message("Request for PI Access", sender=email,recipients=recipients)
            #emailMessage.body = f"Hello Bob and Donna,\n\n {name} is requesting admin access. {name} is from {institution} and reachable at {email}.\n\n You will find their request on the View Requests for Access page in the Heard and Understood App."
            #mail.send(emailMessage)
            print('email sent successfully!')
        except Exception as e:
            print('problem sending email')
            print(e)

        
    return render_template('UserView/pi_access_request.html')


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
            body = f"""Hi You recently requested a password reset for HUA. Your verification code is below.{verification_secret} 
            This code will expire in 15 minutes.If you didn't request a password reset, you can safely disregard this email.
            This account is not monitored, please do not reply to this email."""

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
                    
                    user_status = user_doc.to_dict().get('status')
                    user_name = user_doc.to_dict().get('name')
                    user_institute=user_doc.to_dict().get('Institute')

                    session["user"] = {
                    "name": user_name,
                     "email": email,
                    "status": user_status,
                    "institute":user_institute}

                    
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
######################################


########################HomePage######################################################
def get_projects():
    user = session.get("user")
    user_email=user.get("email")
    
    global project_cache
    
    if (len(project_cache)==0):
        ##Getting all the projects where 
        projects_ref = db.collection("projects")
        query_ref=projects_ref.where(filter=FieldFilter("project_members", "array_contains",user_email)).stream()
    
        ##Keeping only the name of the project
        for doc in  query_ref:
            doc_df=doc.to_dict()
            project_name=doc_df["project_name"]
            project_code = doc_df["project_code"]
    
        project_cache.append({
        "project_name": project_name,
        "project_code": project_code
        })
           
           

   
    return project_cache
    
@app.route("/homepage", methods=['GET', 'POST'])
def homepage():

    user = session.get("user")
    user_email=user.get("email")
    user_status=user.get("status")

    all_projects=get_projects()
   
       
    if request.method=="POST":
        access_code=request.form.get('accessCode')
        
        projects_ref = db.collection("projects")
        query_ref=projects_ref.where(filter=FieldFilter("access_code", "==",access_code)).stream()

        if any(query_ref):
            for doc in query_ref:
                doc_ref = db.collection("projects").document(doc.id)
                doc_ref.update({'project_members': firestore.ArrayUnion([user_email])})
        else:
            flash("This project does not exist", "danger")
            

   
    ##Redirects to the correct page given status
    if user_status=="Admin":
        return render_template('AdminView/homeAdmin.html',projects=all_projects)
    elif user_status=="PI":
        return render_template('PIView/homePI.html',projects=all_projects)
    else:
        return render_template('UserView/homeUser.html',projects=all_projects)

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
    session.clear()
    return url_for('login')


@app.route('/contact')
def contact():
    all_projects=get_projects()
    return render_template('PIView/contact-admin.html',projects=all_projects)

@app.route("/profile", methods=["POST", "GET"])
def profile():
    user = session.get("user")
    user_status= user.get("status")
    user_email=user.get("email")
    user_name=user.get("name")
    user_institute=user.get("institute")

    all_projects=get_projects()

    if user_status=="User":
        return render_template("UserView/UserProfile.html",email=user_email,name=user_name,institute=user_institute,projects=all_projects)
    elif user_status=="PI":
        return render_template("PIView/PIProfile.html",email=user_email,name=user_name,institute=user_institute,projects=all_projects)
    else:
        return render_template("AdminView/AdminProfile.html",email=user_email,name=user_name,institute=user_institute,projects=all_projects)

@app.route("/change-profile", methods=['GET', 'POST'])
def change_profile():
    user = session.get("user")
    user_email=user.get("email")
    user_name= user.get("name")
    user_status=user.get("status")
    user_inst=user.get("Institute")

    all_projects=get_projects()
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_email=user.get("email")
        user_name= user.get("name")
        
        if user_email!=email:
            user_ref=db.collection("users").document(email).set({"email":email,"name":name,"password":hashed_password.decode('utf-8')})
            
        else:
            user_ref=db.collection("users").document(user_email)
            user_ref.update({"email":email,"name":name,"password":hashed_password.decode('utf-8')})

        session["user"]["name"]=name
        session["user"]["email"]=email
        flash("Updated Profile Information", "success")
    
    if user_status=="User":
        return render_template("UserView/change-profileUser.html",email=user_email,name=user_name,projects=all_projects)
    elif user_status=="PI":
        return render_template("PIView/change-profilePI.html",email=user_email,name=user_name,projects=all_projects)
    else:
        return render_template("AdminView/change-profileAdmin.html",email=user_email,name=user_name,projects=all_projects)


##Creates new project
@app.route("/generateNewProject", methods=['POST', 'GET'])
def generateNewProject():
    user=session.get("user")
    user_status=user.get("status")
    user_email= user.get("email")

    if request.method=='POST':
        pName=request.form["p_Name"]
        accessCode=secrets.token_hex(3)
        
        project_key =str(uuid.uuid4())
        ##Updates project collection
        project_ref = db.collection("projects").document(project_key)
        project_ref.set({"access_code":accessCode,'project_name':pName,"project_members":[user_email],"PI_email":user_email})
        global project_cache
        project_cache=[]
        
        return redirect(url_for('generateNewProject'))

    else:
        all_projects=get_projects()
        if (user_status=="PI"):
            return render_template('PIView/newProjectPI.html',projects=all_projects)
        else :
            return render_template('AdminView/newProjectAdmin.html',projects=all_projects)
#############################



########################Project View#####################################################

@app.route("/dashboard/<projectCode>")
def dashboard(projectCode):
    user = session.get("user")
    user_status= user.get("status")
    session["project"]=projectCode

    if(user_status=="User"):
        return render_template("UserView/dashboardUser.html")
        
    elif(user_status=="PI"):
        return render_template("PIView/dashboardPI.html")
    else:
        return render_template("AdminView/dashboardAdmin.html")
    
@app.route("/ground_truthing")
def ground_truthing():
    user = session.get("user")
    user_status= user.get("status")
    if(user_status=="User"):
        return render_template("UserView/ground_truthing.html")
        
    elif(user_status=="PI"):
        return render_template("PIView/ground_truthing.html")
    else:
        return render_template("AdminView/ground_truthing.html")

@app.route("/import")
def upload():
    user = session.get("user")
    user_status= user.get("status")
    if (user_status=="User"):
        return render_template('UserView/importPageUser.html')
    elif(user_status=="PI"):
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
    user=session.get("user")
    user_email=user.get("email")
    project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))

    if request.method=='POST':
       
        ##Project name being searched
        searched_name=request.form["s_Name"]
        searched_projects=[]
        query_ref=project_ref.where(filter=FieldFilter("project_name", "==",searched_name)).stream()

        for doc in  query_ref:
         searched_projects.append(doc.to_dict())
        return render_template('PIView/viewAllProjectsAdmin.html',all_project=searched_projects)
    
    else: 
       
        all_project_coll=project_ref.get()
        all_projects=[]

        for doc in all_project_coll:
            project = doc.to_dict()  
            all_projects.append(project)
    
        return render_template('PIView/viewAllProjectsPI.html',all_project=all_projects)
       



@app.route("/deleteProject/<project_name>")
def deleteProject(project_name):
    user=session.get("user")
    user_status=user.get("status")
    user_email=user.get("email")
    project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email)) 
    query_ref=project_ref.where(filter=FieldFilter("project_name", "==",project_name))
    query_ref.delete()

    if user_status=="PI":
        return redirect(url_for('viewAllProjectsPI'))
    else:
        return redirect(url_for('viewAllProjectsAdmin'))
    

##Generates new code for project
@app.route("/generateNewCode/<project_name>")
def generateNewCode(project_name):
    user=session.get("user")
    user_status=user.get("status")
    user_email=user.get("email")
    newCode=secrets.token_hex(3)

    project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))
    
    query_ref=project_ref.where(filter=FieldFilter("project_name", "==",project_name)).stream()
    


    for doc in query_ref:
       doc_ref = db.collection("projects").document(doc.id)
       doc_ref.update({'access_code':newCode})
        


    query_ref.update({'access_code':newCode})
    if(user_status=="PI"):
        return redirect(url_for('PIView/viewAllProjectsPI'))
    else:
        return redirect(url_for('AdminView/viewAllProjectsAdmin'))



@app.route("/groundTruthUpdates")
def groundTruthUpdates():
    user=session.get("user")
    user_status=user.get("status")
    user_email=user.get("email")

    groundTruthing_ref=db.collection("projects")
    groundTruthing_records=[]
   
    query_ref=groundTruthing_ref.where(filter=FieldFilter("PI_email", "==",user_email)).stream()
    for doc in  query_ref:
         ground_truthing_info=doc.to_dict["ground_truthing"]
         groundTruthing_records.append(ground_truthing_info)

    if (user_status=="PI"):  
        return render_template('PIView/groundTruthingRecordsPI.html',all_groundTruth=groundTruthing_records)
    
    else:
        return render_template('AdminView/groundTruthingRecordsAdmin.html',all_groundTruth=groundTruthing_records)
   
    
#-Super PI-#
##Allows super pi to register new PI if an account has not yet been created
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

##Shows request from users want PI statis
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

##Shows every project registered
@app.route("/viewAllProjectsAdmin", methods=['POST', 'GET'])
def viewAllProjectsAdmin():

    user= session.get("user")
    user_email=user.get("email")
    project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))

    if request.method=='POST':
       
        ##Project name being searched
        searched_name=request.form["s_Name"]
        searched_projects=[]
        query_ref=project_ref.where(filter=FieldFilter("project_name", "==",searched_name)).stream()

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

##Shows all existing users
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

