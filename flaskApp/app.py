from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)
