from flask import Flask, render_template, request, redirect, url_for
from db_utils import upload_file_to_db, connect_to_database

app = Flask(__name__)


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
