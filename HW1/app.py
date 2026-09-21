from flask import Flask, render_template

app = Flask(__name__)

NAME = "배병욱"
STUDENT_ID = "21011696"

HOBBIES = ["유튜브 시청", "잠", "야구"]


@app.route("/")
def home():
    return render_template("index.html", name=NAME, student_id=STUDENT_ID)


@app.route("/profile")
def profile():
    return render_template("profile.html", name=NAME, hobbies=HOBBIES)
