from flask import Flask, render_template

app=Flask(__name__)


@app.route("/")
def home():
    return "Testing"

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/algorithm")
def algorithm():
    return "Redirect for running algorithm"

@app.route("/confusionMatrix")
def confusionMatrix():
    return "Redirect for confusion matrix"

@app.route("/rawData")
def rawData():
    return "Redirect for rawData"




if __name__ =="__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=False)

