from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", name="배병욱", student_id="21011696")


@app.route("/profile")
def profile():
    hobbies = ["유튜브 시청", "잠", "야구"]
    return render_template("profile.html", name="배병욱", hobbies=hobbies)


@app.route("/greet/<name>")
def greet(name):
    return render_template("greet.html", name=name)
