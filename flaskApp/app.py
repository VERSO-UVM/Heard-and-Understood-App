from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, json
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from firebase.config import Config
from db_utils import upload_file_to_db, connect_to_database

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

@app.route("/import")
def upload():
    return render_template('importPage.html')

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


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)
