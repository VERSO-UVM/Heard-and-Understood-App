
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