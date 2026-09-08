from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from flask_session import Session
from flask_bootstrap import Bootstrap
import secrets
from datetime import datetime, timezone
import os
import uuid
import pandas as pd
import subprocess

CONSERT_PYTHON = "/opt/homebrew/anaconda3/envs/consert_env/bin/python"
CONSERT_SCRIPT = os.path.join("hua", "consert", "consert_process.py")
CONSERT_OUTPUT_CSV = os.path.join("hua", "static", "test_video_classification.csv")

SPECTROGRAM_CSV = os.path.join("hua", "static", "spectrogram.csv")

PAUSE_CSV_COLUMNS = ['start', 'stop', 'context', 'class', 'pause_type']


def load_pause_data():
    if not os.path.exists(CONSERT_OUTPUT_CSV):
        df = pd.DataFrame(columns=PAUSE_CSV_COLUMNS)
        os.makedirs(os.path.dirname(CONSERT_OUTPUT_CSV), exist_ok=True)
        df.to_csv(CONSERT_OUTPUT_CSV, index=False)
        return df

    df = pd.read_csv(CONSERT_OUTPUT_CSV)

    missing = [col for col in PAUSE_CSV_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Pause CSV is missing expected column(s) {missing}. "
            f"Found columns: {list(df.columns)}")
    return df[PAUSE_CSV_COLUMNS]


# NOTE: Firebase/Firestore and the SQL db_utils layer have been removed.
# Nothing in this file talks to a database. User/project data is kept
# in-memory (module-level lists) and in the Flask session only, which
# means it resets whenever the server restarts. Swap the marked spots
# back to real persistence whenever the db layer comes back online.

USERS = {}
PROJECTS = {}
REQUESTS = {}

DEFAULT_PROJECT_KEY = "default-project"


def ensure_default_project():
    if DEFAULT_PROJECT_KEY not in PROJECTS:
        PROJECTS[DEFAULT_PROJECT_KEY] = {
            "access_code": DEFAULT_PROJECT_KEY,
            "project_name": "Default Project",
            "project_members": [],
            "PI_email": "",
            "ground_truthing": [{}]
        }
    return PROJECTS[DEFAULT_PROJECT_KEY]


def enter_default_project(user_email):
    project = ensure_default_project()
    if user_email and user_email not in project["project_members"]:
        project["project_members"].append(user_email)
    session["project"] = {"access": DEFAULT_PROJECT_KEY}


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-me'
    app.config['SESSION_TYPE'] = 'filesystem'

    Bootstrap(app)
    Session(app)

    @app.route("/")
    def home():
        session.clear()
        get_projects.cache = []
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            Institute = request.form.get('Institute')
            name = request.form.get('name')

            USERS[email] = {
                'email': email,
                'password': password,
                'status': 'User',
                'name': name,
                'Institute': Institute
            }

            session["user"] = {
                "name": name,
                "email": email,
                "status": "User",
                "institute": Institute}

            enter_default_project(email)
            return redirect(url_for('dashboard'))

    @app.route('/forgot_password')
    def forgot_password():
        return render_template('forgot_password.html')

    @app.route('/pi_access_request', methods=['GET', 'POST'])
    def pi_access_request():
        user = session.get("user")
        return render_template('UserView/pi_access_request.html')

    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'POST':
            email = request.form.get('email').strip().lower()

            # No db lookup / no email sending - just move to the next step.
            flash("A verification code has been sent to your email.", "success")
            return redirect(url_for('enter_code', email=email))

        return render_template('reset_password.html')

    @app.route('/enter_code', methods=['GET', 'POST'])
    def enter_code():
        email = request.args.get('email')
        if not email:
            flash("Invalid request.", "danger")
            return redirect(url_for('reset_password'))

        if request.method == 'POST':
            return redirect(url_for('new_password', email=email))

        return render_template('enter_code.html', email=email)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            print("Form Data:", request.form)
            email = request.form.get('email')
            password = request.form.get('password')

            session["user"] = {
                "name": email,
                "email": email,
                "status": "User",
                "institute": ""}

            enter_default_project(email)
            return redirect(url_for('dashboard'))

        return render_template('login.html')

    def get_projects():
        user = session.get("user")
        user_email = user.get("email")

        if not hasattr(get_projects, "cache"):
            get_projects.cache = []

        if len(get_projects.cache) == 0:
            for project in PROJECTS.values():
                if user_email in project.get("project_members", []):
                    get_projects.cache.append({
                        "project_name": project["project_name"],
                        "project_code": project["access_code"]
                    })

        return get_projects.cache

    @app.route("/homepage", methods=['GET', 'POST'])
    def homepage():
        if hasattr(get_projects, "cache"):
            get_projects.cache = []
        user = session.get("user")
        user_email = user.get("email")
        user_status = user.get("status")

        all_projects = get_projects()

        if request.method == "POST":
            access_code = request.form.get('accessCode')

            matched = None
            for project in PROJECTS.values():
                if project.get("access_code") == access_code:
                    matched = project
                    break

            if matched:
                matched.setdefault("project_members", [])
                if user_email not in matched["project_members"]:
                    matched["project_members"].append(user_email)
                get_projects.cache = []
            else:
                flash("This project does not exist", "danger")

        if user_status == "Admin":
            return render_template('AdminView/homeAdmin.html', projects=all_projects)
        elif user_status == "PI":
            return render_template('PIView/homePI.html', projects=all_projects)
        else:
            return render_template('UserView/homeUser.html', projects=all_projects)

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

            # No db write - just update the in-memory user if present.
            if email in USERS:
                USERS[email]['password'] = new_password

            flash("Your password has been successfully reset. You can now log in.", "success")
            return redirect(url_for('home'))

        return render_template('new_password.html', email=email)

    @app.route('/logout')
    def logout():
        session.clear()
        get_projects.cache = []
        return url_for('login')

    @app.route('/contact')
    def contact():
        all_projects = get_projects()
        return render_template('PIView/contact-admin.html', projects=all_projects)

    @app.route("/profile", methods=["POST", "GET"])
    def profile():
        user = session.get("user")
        user_status = user.get("status")
        user_email = user.get("email")
        user_name = user.get("name")
        user_institute = user.get("institute")

        all_projects = get_projects()

        if user_status == "User":
            return render_template("UserView/UserProfile.html", email=user_email, name=user_name, institute=user_institute, projects=all_projects)
        elif user_status == "PI":
            return render_template("PIView/PIProfile.html", email=user_email, name=user_name, institute=user_institute, projects=all_projects)
        else:
            return render_template("AdminView/AdminProfile.html", email=user_email, name=user_name, institute=user_institute, projects=all_projects)

    @app.route("/change-profile", methods=['GET', 'POST'])
    def change_profile():
        user = session.get("user")
        user_email = user.get("email")
        user_name = user.get("name")
        user_status = user.get("status")

        all_projects = get_projects()
        if request.method == 'POST':
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")

            USERS[email] = USERS.pop(user_email, {})
            USERS[email].update({"email": email, "name": name, "password": password})

            session["user"]["name"] = name
            session["user"]["email"] = email
            flash("Updated Profile Information", "success")
            user_email = email
            user_name = name

        if user_status == "User":
            return render_template("UserView/change-profileUser.html", email=user_email, name=user_name, projects=all_projects)
        elif user_status == "PI":
            return render_template("PIView/change-profilePI.html", email=user_email, name=user_name, projects=all_projects)
        else:
            return render_template("AdminView/change-profileAdmin.html", email=user_email, name=user_name, projects=all_projects)


    @app.route("/generateNewProject", methods=['POST', 'GET'])
    def generateNewProject():
        user = session.get("user")
        user_status = user.get("status")
        user_email = user.get("email")

        if request.method == 'POST':
            pName = request.form["p_Name"]
            accessCode = secrets.token_hex(3)

            project_key = str(uuid.uuid4())
            # No db write - store the new project in memory instead.
            PROJECTS[project_key] = {
                "access_code": accessCode,
                "project_name": pName,
                "project_members": [user_email],
                "PI_email": user_email,
                "ground_truthing": [{}]
            }

            return redirect(url_for('generateNewProject'))

        else:
            get_projects.cache = []
            all_projects = get_projects()
            if user_status == "PI":
                return render_template('PIView/newProjectPI.html', projects=all_projects)
            else:
                return render_template('AdminView/newProjectAdmin.html', projects=all_projects)

    @app.route("/projectInfo/<project_code>")
    def projectInfo(project_code):
        session["project"] = {
            "access": project_code}

        return redirect(url_for('dashboard'))

    @app.route("/dashboard")
    def dashboard():
        if hasattr(get_projects, "cache"):
            get_projects.cache = []
        user = session.get("user")
        user_status = user.get("status")

        if user_status == "User":
            return render_template("UserView/dashboardUser.html")
        elif user_status == "PI":
            return render_template("PIView/dashboardPI.html")
        else:
            return render_template("AdminView/dashboardAdmin.html")

    @app.route("/ground_truthing")
    def ground_truthing():
        user = session.get("user")
        user_status = user.get("status")
        if user_status == "User":
            return render_template("UserView/ground_truthing.html")
        elif user_status == "PI":
            return render_template("PIView/ground_truthing.html")
        else:
            return render_template("AdminView/ground_truthing.html")

    @app.route("/import")
    def upload():
        user = session.get("user")
        user_status = user.get("status")
        if user_status == "User":
            return render_template('UserView/importPageUser.html')
        elif user_status == "PI":
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

        upload_dir = os.path.join('hua', 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, file.filename))
        return redirect(url_for('upload'))

    @app.route("/api/uploads")
    def api_uploads():
        upload_dir = os.path.join('hua', 'static', 'uploads')
        files = []
        if os.path.isdir(upload_dir):
            files = sorted(os.listdir(upload_dir))
        return jsonify(files)

    @app.route("/view-files")
    def view_files():
        upload_dir = os.path.join('hua', 'static', 'uploads')
        files = []
        if os.path.isdir(upload_dir):
            files = [(i, name, '') for i, name in enumerate(os.listdir(upload_dir))]
        return render_template('view-files.html', files=files)

    @app.route('/testOutput/<filename>')
    def get_output_file(filename):
        return send_from_directory('test_output', filename)

    @app.route('/run_consert', methods=['POST'])
    def run_consert():
        """Trigger the ConSert process when the button is clicked."""
        data = request.get_json(silent=True) or {}
        recording = data.get('recording')

        if not recording:
            return jsonify({"status": "error", "message": "No recording selected."}), 400

        recording_path = os.path.join('hua', 'static', 'uploads', recording)

        print(f"[ConSert] Running: {CONSERT_PYTHON} {CONSERT_SCRIPT} {recording_path}")

        try:
            result = subprocess.run(
                [CONSERT_PYTHON, CONSERT_SCRIPT, recording_path],
                capture_output=True, text=True, timeout=600
            )
        except FileNotFoundError:
            return jsonify({
                "status": "error",
                "message": f"Couldn't find the conda python at {CONSERT_PYTHON}. "
                           f"Update CONSERT_PYTHON in app.py to match your setup."
            }), 500
        except subprocess.TimeoutExpired:
            return jsonify({"status": "error", "message": "ConSert process timed out."}), 500

        print(f"[ConSert] stdout:\n{result.stdout}")
        print(f"[ConSert] stderr:\n{result.stderr}")

        if result.returncode != 0:
            return jsonify({"status": "error", "message": result.stderr or "ConSert process failed."}), 500

        return jsonify({"status": "success", "message": "Consert process finished!"})

    @app.route('/spectrogram_upload', methods=['POST'])
    def spectrogram_upload():
        """Saves an uploaded spectrogram CSV to a fixed path for the ground-truthing loop view."""
        if 'file' not in request.files:
            return "no file uploaded", 400
        file = request.files['file']
        if file.filename == '':
            return "no file selected", 400
        if file and file.filename.lower().endswith('.csv'):
            file.save(SPECTROGRAM_CSV)
            return ("", 204)
        else:
            return "Invalid, please upload a CSV file.", 400

    @app.route('/api/spectrogram_data')
    def api_spectrogram_data():
        """Returns the uploaded spectrogram as a 2D array: rows[time_frame][frequency_bin].
        Assumes a headerless wide-format CSV - adjust header=None below if yours has a header row."""
        if not os.path.exists(SPECTROGRAM_CSV):
            response = jsonify({"error": "No spectrogram uploaded yet."})
            response.headers['Cache-Control'] = 'no-store'
            return response, 404

        df = pd.read_csv(SPECTROGRAM_CSV, header=None)
        response = jsonify({"rows": df.values.tolist()})
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.route('/api/consert_output')
    def api_consert_output():
        """Reads the script's actual output CSV for the 'View Raw Data' modal."""
        if not os.path.exists(CONSERT_OUTPUT_CSV):
            response = jsonify({"error": "No output yet. Run the algorithm first."})
            response.headers['Cache-Control'] = 'no-store'
            return response, 404

        df = load_pause_data()

        valid_mask = df['start'].notna() & df['stop'].notna()
        skipped_count = int((~valid_mask).sum())
        valid_df = df[valid_mask]
        safe_df = valid_df.astype(object).where(pd.notnull(valid_df), None)

        response = jsonify({
            "columns": list(df.columns),
            "rows": safe_df.to_dict(orient="records"),
            "skipped_count": skipped_count
        })

        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.route('/download_consert_csv')
    def download_consert_csv():
        """Lets 'Download CSV' actually download the script's real output file."""
        if not os.path.exists(CONSERT_OUTPUT_CSV):
            return "No output yet. Run the algorithm first.", 404
        directory = os.path.dirname(os.path.abspath(CONSERT_OUTPUT_CSV))
        filename = os.path.basename(CONSERT_OUTPUT_CSV)
        return send_from_directory(directory, filename, as_attachment=True)


    @app.route("/viewAllProjectsPI", methods=['POST', 'GET'])
    def viewAllProjectsPI():
        user = session.get("user")
        user_email = user.get("email")
        allprojects = get_projects()

        my_projects = [p for p in PROJECTS.values() if p.get("PI_email") == user_email]

        if request.method == 'POST':
            searched_name = request.form["s_Name"]
            searched_projects = [p for p in my_projects if p.get("project_name") == searched_name]
            return render_template('PIView/viewAllProjectsPI.html', all_project=searched_projects, projects=allprojects)
        else:
            return render_template('PIView/viewAllProjectsPI.html', all_project=my_projects, projects=allprojects)

    @app.route("/deleteProject/<project_name>")
    def deleteProject(project_name):
        user = session.get("user")
        user_status = user.get("status")
        user_email = user.get("email")

        to_delete = [k for k, p in PROJECTS.items()
                     if p.get("PI_email") == user_email and p.get("project_name") == project_name]
        for key in to_delete:
            del PROJECTS[key]

        if user_status == "PI":
            return redirect(url_for('viewAllProjectsPI'))
        else:
            return redirect(url_for('viewAllProjectsAdmin'))

    @app.route("/generateNewCode/<project_name>")
    def generateNewCode(project_name):
        user = session.get("user")
        user_status = user.get("status")
        user_email = user.get("email")
        newCode = secrets.token_hex(3)

        for project in PROJECTS.values():
            if project.get("PI_email") == user_email and project.get("project_name") == project_name:
                project["access_code"] = newCode

        if user_status == "PI":
            return redirect(url_for('viewAllProjectsPI'))
        else:
            return redirect(url_for('viewAllProjectsAdmin'))

    @app.route("/groundTruthUpdates")
    def groundTruthUpdates():
        user = session.get("user")
        user_status = user.get("status")

        project = session.get("project")
        access_code = project.get("access")

        groundTruthing_records = []
        for p in PROJECTS.values():
            if p.get("access_code") == access_code:
                groundTruthing_records.append(p.get("ground_truthing", []))

        if user_status == "PI":
            return render_template('PIView/groundTruthingRecordsPI.html', all_groundTruth=groundTruthing_records)
        else:
            return render_template('AdminView/groundTruthingRecordsAdmin.html', all_groundTruth=groundTruthing_records)

    @app.route('/registerNewPI', methods=['GET', 'POST'])
    def registerNewPI():
        allprojects = get_projects()
        if request.method == 'GET':
            return render_template('AdminView/registerNewPi.html', projects=allprojects)
        else:
            email = request.form.get('email')
            Institute = request.form.get('Institute')
            name = request.form.get('name')
            password = request.form.get('password')

            if email in USERS:
                flash("An account with this email already exists.", "danger")
                return redirect(url_for('registerNewPI'))

            USERS[email] = {
                'email': email,
                'password': password,
                'status': 'PI',
                'name': name,
                'Institute': Institute,
                'projects': []
            }

            return redirect(url_for('registerNewPI'))

    @app.route('/piRequest', methods=['GET', 'POST'])
    def piRequest():
        allprojects = get_projects()
        all_request = list(REQUESTS.values())
        return render_template('AdminView/piRequest.html', all_request=all_request, projects=allprojects)

    @app.route("/acceptRequest/<pName>")
    def acceptRequest(pName):
        if pName in USERS:
            USERS[pName]['status'] = 'PI'
        REQUESTS.pop(pName, None)
        return redirect(url_for('piRequest'))

    @app.route("/declineRequest/<pName>")
    def declineRequest(pName):
        REQUESTS.pop(pName, None)
        return redirect(url_for('piRequest'))

    @app.route("/viewAllProjectsAdmin", methods=['POST', 'GET'])
    def viewAllProjectsAdmin():
        user = session.get("user")
        user_email = user.get("email")
        allprojects = get_projects()

        my_projects = [p for p in PROJECTS.values() if p.get("PI_email") == user_email]

        if request.method == 'POST':
            searched_name = request.form["s_Name"]
            searched_projects = [p for p in my_projects if p.get("project_name") == searched_name]
            return render_template('AdminView/viewAllProjectsAdmin.html', all_project=searched_projects, projects=allprojects)
        else:
            return render_template('AdminView/viewAllProjectsAdmin.html', all_project=my_projects, projects=allprojects)

    ##Shows all existing users
    @app.route("/viewAllUsersAdmin", methods=['POST', 'GET'])
    def viewAllUsersAdmin():
        allprojects = get_projects()
        if request.method == 'POST':
            searchedName = request.form["s_Name"]
            found = USERS.get(searchedName)
            searched_users = [found] if found else []
            return render_template('AdminView/viewAllUsersAdmin.html', all_users=searched_users, projects=allprojects)
        else:
            all_users = list(USERS.values())
            return render_template('AdminView/viewAllUsersAdmin.html', all_users=all_users, projects=allprojects)

    @app.route('/add_new_pause', methods=['POST'])
    def add_new_pause():
        pause_classes = ['non-connectional', 'emotional', 'invitational']

        modifications = load_pause_data()

        start_time = float(request.form.get('startTime'))
        end_time = float(request.form.get('endTime'))

        pause_type = request.form.get('new-pause-type')

        transcription = request.form.get('transcription')

        pause_class = float(pause_classes.index(pause_type))

        if start_time < end_time:
            new_row = pd.DataFrame(
                [[start_time, end_time, transcription, pause_class, pause_type]],
                columns=PAUSE_CSV_COLUMNS)
            modifications = pd.concat([modifications, new_row], ignore_index=True)
            modifications = modifications.sort_values(by='start')
            modifications.to_csv(CONSERT_OUTPUT_CSV, index=False)

        return ("", 204)

    @app.route('/extend_clip', methods=['POST'])
    def extend_clip():
        pause_classes = ['non-connectional', 'emotional', 'invitational']

        change_start_time = False
        change_end_time = False
        edit_transcript = False
        modify_pause_type = False

        input_time = float(request.form.get('pauseAt'))

        if request.form.get('modifyStartTime'):
            start_time = float(request.form.get('modifyStartTime'))
            change_start_time = True

        if request.form.get('modifyEndTime'):
            end_time = float(request.form.get('modifyEndTime'))
            change_end_time = True

        if request.form.get('editTranscription'):
            transcription = request.form.get('editTranscription')
            edit_transcript = True

        if request.form.get('modify-pause-type'):
            pause_type = request.form.get('modify-pause-type')
            modify_pause_type = True

        modifications = load_pause_data()
        found_pause = False
        pause_index = -1

        try:
            if change_start_time and change_end_time:
                assert start_time < end_time, "Start time must be less than end time. "
        except AssertionError as message:
            print(message)

        for i, row in modifications.iterrows():
            if input_time >= float(row['start']) and input_time <= float(row['stop']):
                found_pause = True
                pause_index = i

        if found_pause:
            if change_start_time:
                modifications.at[pause_index, 'start'] = start_time
            if change_end_time:
                modifications.at[pause_index, 'stop'] = end_time
            if edit_transcript:
                modifications.at[pause_index, 'context'] = transcription
            if modify_pause_type:
                modifications.at[pause_index, 'pause_type'] = pause_type
                modifications.at[pause_index, 'class'] = pause_classes.index(pause_type)

            modifications = modifications.sort_values(by='start')
            modifications.to_csv(CONSERT_OUTPUT_CSV, index=False)

        return ("", 204)

    @app.route('/delete_pause', methods=['POST'])
    def delete_pause():
        input_time = float(request.form.get('pauseAtDelete'))
        modifications = load_pause_data()

        found_pause = False
        pause_index = -1
        for i, row in modifications.iterrows():
            if input_time >= float(row['start']) and input_time <= float(row['stop']):
                found_pause = True
                pause_index = i

        if found_pause:
            modifications = modifications.drop(pause_index)
            modifications.to_csv(CONSERT_OUTPUT_CSV, index=False)

        return ("", 204)

    @app.route('/save_changes', methods=['POST'])
    def ground_truth_connection():
        project = session.get("project")
        access_code = project.get("access")
        user = session.get("user")
        user_name = user.get("name")

        data = request.get_json(silent=True) or {}
        pauses = data.get("pauses")
        if pauses is not None:
            df = pd.DataFrame(pauses, columns=PAUSE_CSV_COLUMNS)
            if not df.empty:
                df = df.sort_values(by='start')
            df.to_csv(CONSERT_OUTPUT_CSV, index=False)

        for p in PROJECTS.values():
            if p.get("access_code") == access_code:
                p.setdefault("ground_truthing", []).append(
                    {"time": datetime.now(timezone.utc), "name": user_name})
                break

        return ("", 204)

    @app.route('/csv_upload', methods=['POST'])
    def csv_upload():
        if 'file' not in request.files:
            return "no file uploaded", 400
        file = request.files['file']
        if file.filename == '':
            return "no file selected", 400
        if file and file.filename.endswith('.csv'):
            file.save(os.path.join('hua/static', 'test_video_classification.csv'))
            return ground_truthing()
        else:
            return "Invalid, please upload a CSV file.", 400

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)