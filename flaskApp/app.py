from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import credentials

app = Flask(__name__)

# Configure Flask-Mail email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP email server 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = credentials.hua_email
app.config['MAIL_PASSWORD'] = credentials.hua_password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


@app.route("/")
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    # password = request.form.get('password')
    return redirect(url_for('homepage', email=email))

@app.route('/send_admin_request_email')
def send_admin_request_email():
    email = request.args["email"]
    recipients = credentials.recipients

    # Create a Message object with subject, sender, and recipient list
    msg = Message(subject='Request Made for HUA Admin Access',
                  sender=credentials.hua_email,
                  recipients=recipients)  
    
    # Email body
    msg.body = f'Hello Bob and Donna,\n\nUser with account: {email} is requesting admin access.'
    
    # Send the email
    mail.send(msg)
    
    return redirect(url_for("homepage", email=email))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/ground_truthing")
def ground_truthing():
    return render_template("ground_truthing.html")

@app.route("/homepage")
def homepage():
    email = request.args["email"]
    return render_template('home.html', email=email)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)
