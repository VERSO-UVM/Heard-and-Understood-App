from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, json
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt, secrets
from firebase.config import Config
from db_utils import upload_file_to_db, connect_to_database
from flask_mail import Mail, Message
import email_credentials
from datetime import datetime, timedelta, timezone

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

# Configure Flask-Mail email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP email server 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = email_credentials.hua_email
app.config['MAIL_PASSWORD'] = email_credentials.hua_password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


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
            recipients = email_credentials.recipients

            emailMessage = Message("Request for PI Access", sender=email,recipients=recipients)
            emailMessage.body = f"Hello Bob and Donna,\n\n {name} is requesting admin access. {name} is from {institution} and reachable at {email}.\n\n You will find their request on the View Requests for Access page in the Heard and Understood App."
            mail.send(emailMessage)
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
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password_bytes):
                        flash("Logged in successfully.", "success")
                        return redirect(url_for('homepage', email=email))
                    else:
                        flash("Invalid password", "danger")
                        return redirect(url_for('login'))

                else:
                    flash("Password not set for this account.", "danger")
                    return redirect(url_for('login'))
            else:
                flash("User not found", "danger")
                return redirect(url_for('login'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('login'))
    
    # Handle GET requests
    return render_template('login.html')


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/ground_truthing")
def ground_truthing():
    return render_template("ground_truthing.html")

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

