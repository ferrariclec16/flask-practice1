from flask import Flask, render_template

app = Flask(__name__)

NAME = "배병욱"
STUDENT_ID = "21011696"


@app.route("/")
def home():
    return render_template("index.html", name=NAME, student_id=STUDENT_ID)
