from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine

engine = create_engine("sqlite://", echo=True, future=True)

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "KoyKoyKoy"
app.permanent_session_lifetime = timedelta(days=365)

class users(db.Model):
    _id = db.Column("id" ,db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, name, email):
        self.name = name
        self.email = email

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/view", methods=["GET", "POST"])
def view():
    user = session["user"]
    print("user:", user)
    values=users.query.all()
    print("values:", values)
    found_user = users.query.filter_by(name=user)
    print("found_user:", found_user)
    if request.method == "POST":
        for user in found_user:
            user.delete()

    else:
        print("view:", values)
        return render_template("view.html", values=values)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.permanent = True
        user = request.form["name"]
        session["user"] = user

        found_user = users.query.filter_by(name=user).first()
        if found_user:
            session["email"] = found_user.email
        else:
            usr = users(user, "")
            db.session.add(usr)
            db.session.commit()
        flash("Login Successful!")
        return redirect(url_for("user"))
    else:
        if "user" in session:
            flash("You are already logged in!")
            return render_template(url_for("user"))
        return render_template("login.html")

@app.route("/user", methods=["GET", "POST"])
def user():
    if "user" in session:
        user = session["user"]
        print(user)

        if request.method == "POST":
            print("post")
            email = request.form["email"]
            session['email'] = email
            found_user = users.query.filter_by(name=user).first()
            found_user.email = email
            db.session.commit()
            flash("Email was saved!")
        else:
            if "email" in session:
                email = session["email"]
        return render_template("user.html", email=email)
    else:
        flash("You are not logged in!")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash('You have been logged out')
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/quote")
def quote():
    return render_template("quote.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



'''

'''




