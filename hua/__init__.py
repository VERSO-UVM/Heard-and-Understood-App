from flask import Flask, render_template, request, redirect, url_for, flash, json, jsonify, session, abort, g, Response
from flask_session import Session
import firebase_admin
from flask_bootstrap import Bootstrap
from firebase_admin import credentials, firestore
import bcrypt, secrets
from google.cloud.firestore_v1.base_query import FieldFilter
from hua.firebase.config import Config
from hua.db_utils import connect_to_database
from flask_mail import Mail, Message
from datetime import datetime, timedelta, timezone
from functools import wraps
import io
import math
import os
import re
import threading
import uuid
import subprocess
import pandas as pd
from werkzeug.utils import secure_filename

ROLES = ("User", "PI", "Admin")
PAUSE_TYPES = ['non-connectional', 'emotional', 'invitational']  # index is the pause class
PAUSE_CSV_COLUMNS = ['start', 'stop', 'context', 'class', 'pause_type']
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.mp4', '.ogg', '.flac', '.webm'}
MIN_PASSWORD_LENGTH = 6
MAX_CODE_ATTEMPTS = 5

# Recordings and transcripts can contain PHI, so each project's files are kept in
# instance/projects/<project id>/ (outside hua/static) and only served to project members.
DATA_DIR = os.path.join("instance", "projects")
CONSERT_PYTHON = os.environ.get("CONSERT_PYTHON", "python")
CONSERT_SCRIPT = os.path.join("hua", "consert", "consert_process.py")


def valid_email(email):
    """Basic shape check; also keeps values usable as Firestore document ids."""
    return bool(email) and re.fullmatch(r"[^@\s/]+@[^@\s/]+\.[^@\s/]+", email) is not None


def project_file(name):
    """Path to a file in the open project's data folder (set by project_required)."""
    return os.path.join(g.project_dir, name)


def load_pause_data():
    df = pd.read_csv(project_file("pause_data.csv"))
    missing = [col for col in PAUSE_CSV_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Pause CSV is missing expected column(s) {missing}.")
    return df[PAUSE_CSV_COLUMNS]


def parse_pauses(pauses):
    """Validates a list of pause dicts and returns a sorted DataFrame. Raises ValueError naming the bad row."""
    if not isinstance(pauses, list):
        raise ValueError("Expected a list of pauses.")
    rows = []
    for i, pause in enumerate(pauses, start=1):
        try:
            start = float(pause["start"])
            stop = float(pause["stop"])
            pause_type = pause["pause_type"]
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"Row {i}: start and stop must be numbers and pause_type is required.")
        if not (math.isfinite(start) and math.isfinite(stop) and 0 <= start < stop):
            raise ValueError(f"Row {i}: start must be less than stop.")
        if pause_type not in PAUSE_TYPES:
            raise ValueError(f"Row {i}: pause_type must be one of {', '.join(PAUSE_TYPES)}.")
        context = pause.get("context")
        if context is None or (isinstance(context, float) and math.isnan(context)):
            context = ""
        rows.append([start, stop, str(context), float(PAUSE_TYPES.index(pause_type)), pause_type])
    return pd.DataFrame(rows, columns=PAUSE_CSV_COLUMNS).sort_values(by='start')


def escape_formula(value):
    """Stops spreadsheet apps from running cell text like =HYPERLINK(...) as a formula."""
    return "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value


def login_required(*roles):
    """Redirects anonymous users to login and returns 403 if the user's status isn't in roles."""
    allowed = roles or ROLES

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for('login'))
            if user.get("status") not in allowed:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def initialize_firebase():
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # load firebase credentials
    with open('serviceAccountKey.json') as f:
        service_account = json.load(f)
        app.secret_key = service_account.get("secret_key")

    # initialize firebase
    initialize_firebase()
    db = firestore.client()

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP email server
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    mail = Mail(app)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Set HUA_SECURE_COOKIES=1 when served over HTTPS
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get("HUA_SECURE_COOKIES") == "1"
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB upload limit

    Bootstrap(app)
    Session(app)

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response

    def project_required(view):
        """Only lets members (or admins) of the open project through; sets g.project_dir."""
        @wraps(view)
        def wrapped(*args, **kwargs):
            project = session.get("project")
            user = session["user"]
            doc = db.collection("projects").document(project["id"]).get() if project else None
            if not doc or not doc.exists or (user["status"] != "Admin" and user["email"] not in doc.to_dict().get("project_members", [])):
                return "Open a project you belong to first.", 403
            g.project_id = doc.id
            g.project_dir = os.path.join(DATA_DIR, secure_filename(doc.id))
            os.makedirs(g.project_dir, exist_ok=True)
            return view(*args, **kwargs)
        return wrapped

    consert_lock = threading.Lock()


    ##########################Login/Register Pages################################################

    @app.route("/")
    def home():
        session.clear()
        return render_template('login.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            Institute=request.form.get('Institute')
            name=request.form.get('name')

            if not valid_email(email):
                flash("Please enter a valid email address.", "danger")
                return redirect(url_for('register'))
            if len(password) < MIN_PASSWORD_LENGTH:
                flash(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.", "danger")
                return redirect(url_for('register'))

            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())

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
            app.session_interface.regenerate(session)

            return redirect(url_for('homepage'))

    @app.route('/forgot_password')
    def forgot_password():
        return render_template('forgot_password.html')

    @app.route('/pi_access_request', methods=['GET', 'POST'])
    @login_required("User")
    def pi_access_request():

        user=session.get("user")
        user_email=user.get("email")
        user_name=user.get("name")
        user_inst=user.get("institute")

        if request.method == 'POST':
            # Add request to HUA firebase
            db.collection('request').document(user_email).set({"email":user_email,"name":user_name})
            try:
                import email_credentials

                # Send email
                recipients = email_credentials.recipients

                emailMessage = Message("Request for PI Access", sender="Huaverso@gmail.com", reply_to=user_email, recipients=recipients)
                emailMessage.body = f"Hello Bob and Donna,\n\n {user_name} is requesting admin access. {user_name} is from {user_inst} and reachable at {user_email}.\n\n You will find their request on the View Requests for Access page in the Heard and Understood App."
                mail.send(emailMessage)
            except Exception as e:
                print('problem sending email:', e)

        return render_template('UserView/pi_access_request.html')


    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            if valid_email(email):
                user_ref = db.collection('users').document(email)
                if user_ref.get().exists:
                    verification_secret = secrets.token_hex(4)
                    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                    user_ref.update({
                        'verification_code': verification_secret,
                        'verification_expiry': expiration_time,
                        'verification_attempts': 0
                    })

                    subject = "HUA Password Reset"
                    body = f"""Hi You recently requested a password reset for HUA. Your verification code is below.{verification_secret}
                    This code will expire in 15 minutes.If you didn't request a password reset, you can safely disregard this email.
                    This account is not monitored, please do not reply to this email."""

                    try:
                        msg = Message(subject, sender="Huaverso@gmail.com", recipients=[email], body=body)
                        mail.send(msg)
                    except Exception as e:
                        print('problem sending reset email:', e)

            # Same response whether or not the account exists, so emails can't be enumerated
            flash("If an account exists for that email, a verification code has been sent.", "success")
            return redirect(url_for('enter_code', email=email))

        return render_template('reset_password.html')

    @app.route('/enter_code', methods=['GET', 'POST'])
    def enter_code():
        email = request.args.get('email')
        if not email:
            flash("Invalid request.", "danger")
            return redirect(url_for('reset_password'))

        if request.method == 'POST':
            entered_code = request.form.get('verification_code', '').strip()
            user_doc = db.collection('users').document(email).get() if valid_email(email) else None
            user_data = user_doc.to_dict() if user_doc and user_doc.exists else {}
            user_ref = db.collection('users').document(email) if user_data else None

            stored_code = user_data.get('verification_code')
            expiry_time = user_data.get('verification_expiry')
            clear_code = {
                'verification_code': firestore.DELETE_FIELD,
                'verification_expiry': firestore.DELETE_FIELD,
                'verification_attempts': firestore.DELETE_FIELD
            }

            if not stored_code or not expiry_time or datetime.now(timezone.utc) > expiry_time:
                if user_ref and stored_code:
                    user_ref.update(clear_code)
                flash("Invalid or expired code. Please request a new one.", "danger")
                return redirect(url_for('reset_password'))

            if not secrets.compare_digest(entered_code.encode('utf-8'), stored_code.encode('utf-8')):
                user_ref.update({'verification_attempts': firestore.Increment(1)})
                if user_data.get('verification_attempts', 0) + 1 >= MAX_CODE_ATTEMPTS:
                    user_ref.update(clear_code)
                    flash("Too many incorrect attempts. Please request a new code.", "danger")
                    return redirect(url_for('reset_password'))
                flash("Invalid verification code.", "danger")
                return redirect(url_for('enter_code', email=email))

            # Codes are single use; the verified email is kept in this browser's session only
            user_ref.update(clear_code)
            session["reset_email"] = email
            return redirect(url_for('new_password'))

        return render_template('enter_code.html', email=email)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            user_data = {}
            if valid_email(email):
                user_doc = db.collection('users').document(email).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()

            stored_hashed_password = user_data.get('password')
            if stored_hashed_password and bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                session.clear()
                session["user"] = {
                    "name": user_data.get('name'),
                    "email": email,
                    "status": user_data.get('status'),
                    "institute": user_data.get('Institute')}
                app.session_interface.regenerate(session)
                return redirect(url_for('homepage'))

            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

        # Handle GET requests
        return render_template('login.html')
    ######################################


    ########################HomePage######################################################
    def get_projects():
        """Name and access code of every project the logged in user belongs to."""
        user_email = session["user"]["email"]
        projects_ref = db.collection("projects")
        query_ref = projects_ref.where(filter=FieldFilter("project_members", "array_contains", user_email)).stream()
        return [{"project_name": doc.to_dict()["project_name"], "project_code": doc.to_dict()["access_code"]}
                for doc in query_ref]

    @app.route("/homepage", methods=['GET', 'POST'])
    @login_required()
    def homepage():
        user = session.get("user")
        user_email=user.get("email")
        user_status=user.get("status")

        if request.method=="POST":
            access_code=request.form.get('accessCode')

            projects_ref = db.collection("projects")
            query_ref=projects_ref.where(filter=FieldFilter("access_code", "==",access_code)).limit(1)
            docs=list(query_ref.stream())

            if docs:
                docs[0].reference.update({'project_members': firestore.ArrayUnion([user_email])})
            else:
                flash("This project does not exist", "danger")

        all_projects=get_projects()

        ##Redirects to the correct page given status
        if user_status=="Admin":
            return render_template('AdminView/homeAdmin.html',projects=all_projects)
        elif user_status=="PI":
            return render_template('PIView/homePI.html',projects=all_projects)
        else:
            return render_template('UserView/homeUser.html',projects=all_projects)

    @app.route('/new_password', methods=['GET', 'POST'])
    def new_password():
        email = session.get("reset_email")
        if not email:
            flash("Please verify your email before choosing a new password.", "danger")
            return redirect(url_for('reset_password'))

        if request.method == 'POST':
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for('new_password'))

            if len(new_password) < MIN_PASSWORD_LENGTH:
                flash(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.", "danger")
                return redirect(url_for('new_password'))

            # Hash the new password and decode to store as string
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.collection('users').document(email).update({'password': hashed_password})
            session.pop("reset_email")

            flash("Your password has been successfully reset. You can now log in.", "success")
            return redirect(url_for('home'))

        return render_template('new_password.html', email=email)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))


    @app.route('/contact')
    @login_required()
    def contact():
        all_projects=get_projects()
        return render_template('PIView/contact-admin.html',projects=all_projects)

    @app.route("/profile", methods=["POST", "GET"])
    @login_required()
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
    @login_required()
    def change_profile():
        user = session.get("user")
        user_email=user.get("email")
        user_name= user.get("name")
        user_status=user.get("status")

        if request.method == 'POST':
            name = request.form.get("name")
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            new_ref = db.collection("users").document(email) if valid_email(email) else None
            if new_ref is None:
                flash("Please enter a valid email address.", "danger")
            elif email != user_email and new_ref.get().exists:
                flash("An account with this email already exists.", "danger")
            elif len(password) < MIN_PASSWORD_LENGTH:
                flash(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.", "danger")
            else:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                old_ref = db.collection("users").document(user_email)
                user_data = old_ref.get().to_dict() or {}
                user_data.update({"email": email, "name": name, "password": hashed_password})

                if email != user_email:
                    ##Moves the account to the new email, keeping status/institute and project membership
                    new_ref.set(user_data)
                    old_ref.delete()
                    member_query = db.collection("projects").where(filter=FieldFilter("project_members", "array_contains", user_email)).stream()
                    for doc in member_query:
                        members = [email if m == user_email else m for m in doc.to_dict().get("project_members", [])]
                        doc.reference.update({"project_members": members})
                    pi_query = db.collection("projects").where(filter=FieldFilter("PI_email", "==", user_email)).stream()
                    for doc in pi_query:
                        doc.reference.update({"PI_email": email})
                    old_request = db.collection("request").document(user_email)
                    if old_request.get().exists:
                        db.collection("request").document(email).set({**old_request.get().to_dict(), "email": email, "name": name})
                        old_request.delete()
                else:
                    old_ref.update(user_data)

                session["user"] = {**user, "name": name, "email": email}
                user_email, user_name = email, name
                flash("Updated Profile Information", "success")

        all_projects=get_projects()
        if user_status=="User":
            return render_template("UserView/change-profileUser.html",email=user_email,name=user_name,projects=all_projects)
        elif user_status=="PI":
            return render_template("PIView/change-profilePI.html",email=user_email,name=user_name,projects=all_projects)
        else:
            return render_template("AdminView/change-profileAdmin.html",email=user_email,name=user_name,projects=all_projects)


    ##Creates new project
    @app.route("/generateNewProject", methods=['POST', 'GET'])
    @login_required("PI", "Admin")
    def generateNewProject():
        user=session.get("user")
        user_status=user.get("status")
        user_email= user.get("email")

        if request.method=='POST':
            pName=request.form["p_Name"]
            accessCode=secrets.token_hex(4)

            project_key =str(uuid.uuid4())
            ##Updates project collection
            project_ref = db.collection("projects").document(project_key)
            project_ref.set({"access_code":accessCode,'project_name':pName,"project_members":[user_email],"PI_email":user_email,"ground_truthing":[{}]})

            return redirect(url_for('generateNewProject'))

        else:
            all_projects=get_projects()
            if (user_status=="PI"):
                return render_template('PIView/newProjectPI.html',projects=all_projects)
            else :
                return render_template('AdminView/newProjectAdmin.html',projects=all_projects)
    #############################



    ########################Project View#####################################################
    @app.route("/projectInfo/<project_code>")
    @login_required()
    def projectInfo(project_code):
        user = session.get("user")
        query_ref = db.collection("projects").where(filter=FieldFilter("access_code", "==", project_code)).limit(1)
        docs = list(query_ref.stream())

        ##Only members (or admins) can open a project
        if not docs or (user["status"] != "Admin" and user["email"] not in docs[0].to_dict().get("project_members", [])):
            flash("You don't have access to that project.", "danger")
            return redirect(url_for('homepage'))

        session["project"] = {
                        "access": project_code,
                        "id": docs[0].id}

        return redirect(url_for('dashboard'))


    @app.route("/dashboard")
    @login_required()
    def dashboard():
        user = session.get("user")
        user_status= user.get("status")

        if(user_status=="User"):
            return render_template("UserView/dashboardUser.html")
        elif(user_status=="PI"):
            return render_template("PIView/dashboardPI.html")
        else:
            return render_template("AdminView/dashboardAdmin.html")

    @app.route("/ground_truthing")
    @login_required()
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
    @login_required()
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
    @login_required()
    @project_required
    def upload_file():
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        file_name = secure_filename(file.filename or '')
        if not file_name:
            return "No file selected", 400
        if os.path.splitext(file_name)[1].lower() not in AUDIO_EXTENSIONS:
            return "Please upload an audio file (" + ", ".join(sorted(AUDIO_EXTENSIONS)) + ").", 400
        os.makedirs(project_file("uploads"), exist_ok=True)
        file.save(os.path.join(project_file("uploads"), file_name))
        return redirect(url_for('upload'))

    @app.route("/view-files")
    @login_required("Admin")
    def view_files():
        connection = connect_to_database()
        if connection is None:
            return "Database connection failed", 500

        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("select id, file_name, file_type from audio_files")
            files = cursor.fetchall()
            return render_template('view-files.html', files=files)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    ##Lists recordings saved to the uploads folder for the dashboard dropdown
    @app.route("/api/uploads")
    @login_required()
    @project_required
    def api_uploads():
        files = []
        if os.path.isdir(project_file("uploads")):
            files = sorted(os.listdir(project_file("uploads")))
        return jsonify(files)

    @app.route('/run_consert', methods=['POST'])
    @login_required()
    @project_required
    def run_consert():
        """Trigger the ConSert process when the button is clicked."""
        data = request.get_json(silent=True) or {}
        recording = secure_filename(data.get('recording') or '')
        recording_path = os.path.join(project_file("uploads"), recording)

        if not recording or not os.path.isfile(recording_path):
            return jsonify({"status": "error", "message": "No recording selected."}), 400

        ##One run at a time; each run can take several minutes
        if not consert_lock.acquire(blocking=False):
            return jsonify({"status": "error", "message": "ConSert is already running. Please try again when it finishes."}), 409
        try:
            result = subprocess.run(
                [CONSERT_PYTHON, CONSERT_SCRIPT, recording_path],
                capture_output=True, text=True, timeout=600
            )
        except FileNotFoundError:
            print(f"ConSert python not found at {CONSERT_PYTHON}; set the CONSERT_PYTHON environment variable.")
            return jsonify({"status": "error", "message": "ConSert is not set up on the server."}), 500
        except subprocess.TimeoutExpired:
            return jsonify({"status": "error", "message": "ConSert process timed out."}), 500
        finally:
            consert_lock.release()

        if result.returncode != 0:
            print(f"ConSert exited with code {result.returncode}")
            return jsonify({"status": "error", "message": "ConSert process failed."}), 500

        return jsonify({"status": "success", "message": "Consert process finished!"})

    ##Saves a spectrogram CSV for the ground truthing loop view
    @app.route('/spectrogram_upload', methods=['POST'])
    @login_required()
    @project_required
    def spectrogram_upload():
        file = request.files.get('file')
        if not file or not file.filename.lower().endswith('.csv'):
            return "Invalid, please upload a CSV file.", 400
        try:
            df = pd.read_csv(file, header=None).apply(pd.to_numeric, errors='raise')
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError):
            df = None
        if df is None or df.isnull().values.any():
            return "Spectrogram CSV must contain only numbers, with no header row or blank cells.", 400
        df.to_csv(project_file("spectrogram.csv"), header=False, index=False)
        return ("", 204)

    ##Returns the spectrogram as rows[time_frame][frequency_bin] (headerless CSV)
    @app.route('/api/spectrogram_data')
    @login_required()
    @project_required
    def api_spectrogram_data():
        if not os.path.exists(project_file("spectrogram.csv")):
            return jsonify({"error": "No spectrogram uploaded yet."}), 404
        df = pd.read_csv(project_file("spectrogram.csv"), header=None)
        response = jsonify({"rows": df.values.tolist()})
        response.headers['Cache-Control'] = 'no-store'
        return response

    ##Returns the current pause CSV for the raw data modal and ground truthing table
    @app.route('/api/consert_output')
    @login_required()
    @project_required
    def api_consert_output():
        if not os.path.exists(project_file("pause_data.csv")):
            return jsonify({"error": "No output yet. Run the algorithm first."}), 404

        try:
            df = load_pause_data()
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as e:
            return jsonify({"error": f"Couldn't read the pause data: {e}"}), 422
        valid_mask = df['start'].notna() & df['stop'].notna()
        valid_df = df[valid_mask]
        safe_df = valid_df.astype(object).where(pd.notnull(valid_df), None)

        response = jsonify({
            "columns": list(df.columns),
            "rows": safe_df.to_dict(orient="records"),
            "skipped_count": int((~valid_mask).sum())
        })
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.route('/download_consert_csv')
    @login_required()
    @project_required
    def download_consert_csv():
        if not os.path.exists(project_file("pause_data.csv")):
            return "No output yet. Run the algorithm first.", 404
        df = pd.read_csv(project_file("pause_data.csv"))
        if 'context' in df.columns:
            df['context'] = df['context'].map(escape_formula)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return Response(buffer.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=pause_data.csv"})



    #-----------------PI View-----------------------#


    ##Allows PI to see every project
    @app.route("/viewAllProjectsPI", methods=['POST', 'GET'])
    @login_required("PI")
    def viewAllProjectsPI():
        user=session.get("user")
        user_email=user.get("email")
        project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))

        allprojects=get_projects()
        if request.method=='POST':
            ##Project name being searched
            searched_name=request.form["s_Name"]
            query_ref=project_ref.where(filter=FieldFilter("project_name", "==",searched_name)).stream()
            searched_projects=[doc.to_dict() for doc in query_ref]
            return render_template('PIView/viewAllProjectsPI.html',all_project=searched_projects,projects=allprojects)

        all_projects=[doc.to_dict() for doc in project_ref.get()]
        return render_template('PIView/viewAllProjectsPI.html',all_project=all_projects,projects=allprojects)


    @app.route("/deleteProject/<project_name>", methods=['POST'])
    @login_required("PI", "Admin")
    def deleteProject(project_name):
        user=session.get("user")
        user_status=user.get("status")
        user_email=user.get("email")
        project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))
        query_ref=project_ref.where(filter=FieldFilter("project_name", "==",project_name)).stream()
        for doc in query_ref:
            doc.reference.delete()

        if user_status=="PI":
            return redirect(url_for('viewAllProjectsPI'))
        else:
            return redirect(url_for('viewAllProjectsAdmin'))


    ##Generates new code for project
    @app.route("/generateNewCode/<project_name>", methods=['POST'])
    @login_required("PI", "Admin")
    def generateNewCode(project_name):
        user=session.get("user")
        user_status=user.get("status")
        user_email=user.get("email")
        newCode=secrets.token_hex(4)

        project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))
        query_ref=project_ref.where(filter=FieldFilter("project_name", "==",project_name)).stream()
        for doc in query_ref:
            doc.reference.update({'access_code':newCode})

        if(user_status=="PI"):
            return redirect(url_for('viewAllProjectsPI'))
        else:
            return redirect(url_for('viewAllProjectsAdmin'))



    @app.route("/groundTruthUpdates")
    @login_required("PI", "Admin")
    @project_required
    def groundTruthUpdates():
        user_status=session["user"].get("status")

        project_doc=db.collection("projects").document(g.project_id).get()
        groundTruthing_records=[project_doc.to_dict().get("ground_truthing", [])]

        if (user_status=="PI"):
            return render_template('PIView/groundTruthingRecordsPI.html',all_groundTruth=groundTruthing_records)
        else:
            return render_template('AdminView/groundTruthingRecordsAdmin.html',all_groundTruth=groundTruthing_records)


    #-Super PI-#
    ##Allows super pi to register new PI if an account has not yet been created
    @app.route('/registerNewPI', methods=['GET', 'POST'])
    @login_required("Admin")
    def registerNewPI():
        allprojects=get_projects()
        if request.method == 'GET':
            return render_template('AdminView/registerNewPi.html',projects=allprojects)
        else:
            email = request.form.get('email', '').strip()
            Institute = request.form.get('Institute')
            name = request.form.get('name')
            password = request.form.get('password', '')

            if not valid_email(email):
                flash("Please enter a valid email address.", "danger")
                return redirect(url_for('registerNewPI'))
            if len(password) < MIN_PASSWORD_LENGTH:
                flash(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.", "danger")
                return redirect(url_for('registerNewPI'))

            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())

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

    ##Shows request from users want PI statis
    @app.route('/piRequest', methods=['GET','POST'])
    @login_required("Admin")
    def piRequest():
        allprojects=get_projects()
        all_request=[doc.to_dict() for doc in db.collection("request").get()]
        return render_template('AdminView/piRequest.html', all_request=all_request,projects=allprojects)

    @app.route("/acceptRequest/<pName>", methods=['POST'])
    @login_required("Admin")
    def acceptRequest(pName):
        if valid_email(pName):
            request_ref = db.collection("request").document(pName)
            user_ref = db.collection("users").document(pName)
            ##Only existing users who actually asked for PI access can be promoted
            if request_ref.get().exists and user_ref.get().exists:
                user_ref.update({'status':'PI'})
            request_ref.delete()
        return redirect(url_for('piRequest'))

    @app.route("/declineRequest/<pName>", methods=['POST'])
    @login_required("Admin")
    def declineRequest(pName):
        if valid_email(pName):
            db.collection("request").document(pName).delete()
        return redirect(url_for('piRequest'))

    ##Shows the projects this admin leads
    @app.route("/viewAllProjectsAdmin", methods=['POST', 'GET'])
    @login_required("Admin")
    def viewAllProjectsAdmin():

        user= session.get("user")
        user_email=user.get("email")
        project_ref = (db.collection("projects")).where(filter=FieldFilter("PI_email", "==",user_email))
        allprojects=get_projects()

        if request.method=='POST':
            ##Project name being searched
            searched_name=request.form["s_Name"]
            query_ref=project_ref.where(filter=FieldFilter("project_name", "==",searched_name)).stream()
            searched_projects=[doc.to_dict() for doc in query_ref]
            return render_template('AdminView/viewAllProjectsAdmin.html',all_project=searched_projects,projects=allprojects)

        all_projects=[doc.to_dict() for doc in project_ref.get()]
        return render_template('AdminView/viewAllProjectsAdmin.html',all_project=all_projects,projects=allprojects)

    ##Shows all existing users
    @app.route("/viewAllUsersAdmin",methods=['POST', 'GET'])
    @login_required("Admin")
    def viewAllUsersAdmin():
        allprojects=get_projects()
        hidden_fields = ('password', 'verification_code', 'verification_expiry', 'verification_attempts')

        def public_fields(user_data):
            return {k: v for k, v in user_data.items() if k not in hidden_fields}

        if request.method=='POST':
            searchedName=request.form.get("s_Name", "").strip()
            searched_users=[]
            if valid_email(searchedName):
                doc=db.collection("users").document(searchedName).get()
                if doc.exists:
                    searched_users.append(public_fields(doc.to_dict()))
            return render_template('AdminView/viewAllUsersAdmin.html',all_users=searched_users,projects=allprojects)

        all_users=[public_fields(doc.to_dict()) for doc in db.collection("users").get()]
        return render_template('AdminView/viewAllUsersAdmin.html',all_users=all_users,projects=allprojects)



########################## Ground Truthing Logic #########################

    @app.route('/save_changes', methods=['POST'])
    @login_required()
    @project_required
    def ground_truth_connection():
        data = request.get_json(silent=True) or {}
        try:
            modifications = parse_pauses(data.get("pauses"))
        except ValueError as e:
            return str(e), 400

        user_name=session["user"].get("name")
        db.collection("projects").document(g.project_id).update(
            {"ground_truthing": firestore.ArrayUnion([{"time": datetime.now(timezone.utc), "name": user_name}])})

        modifications.to_csv(project_file("pause_data.csv"), index=False)
        return ("", 204)


    @app.route('/csv_upload', methods=['POST'])
    @login_required()
    @project_required
    def csv_upload():
        file = request.files.get('file')
        if not file or not file.filename.lower().endswith('.csv'):
            return "Invalid, please upload a CSV file.", 400
        try:
            df = pd.read_csv(file)
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError):
            return "Couldn't read that CSV file.", 400
        missing = [col for col in PAUSE_CSV_COLUMNS if col not in df.columns]
        if missing:
            return f"CSV is missing column(s): {', '.join(missing)}", 400
        try:
            pauses = parse_pauses(df.to_dict(orient="records"))
        except ValueError as e:
            return str(e), 400
        pauses.to_csv(project_file("pause_data.csv"), index=False)
        return ("", 204)


    return app
