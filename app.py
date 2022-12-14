import os

from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta, date, datetime
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session

from helpers import apology, login_required

# create the app
app = Flask(__name__)

# Session/Cookie configurations
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
# app.config["TEMPLATES_AUTO_RELOAD"] = True

app.secret_key = "KoyKoyKoy"

# Establish connection to database
con = sqlite3.connect("koy.db", check_same_thread=False)
db = con.cursor()

# Create a function that returns all grocery-entries from database
def get_db():
    db.execute("select name from groceries")
    all_data = db.fetchall()
    all_data = [str(val[0]) for val in all_data]

    # make a copy of the list which contains only the first database entry
    shopping_list = all_data.copy() 
    shopping_list = shopping_list[0:1]

    return all_data, shopping_list

# In the index route it is possible to add and remove items. The further routes (see routes below) "/add_items" and "/remove_items" return index.html
@app.route("/", methods=["GET", "POST"])
def home():
    # store the two lists in session so the other routes can access them
    session["all_items"], session["shopping_items"] = get_db()
    return render_template("index.html", all_items=session["all_items"], shopping_items=session["shopping_items"])


@app.route("/add_items", methods=["POST"])
def add_items():
    session["shopping_items"].append(request.form["select_items"])
    return render_template("index.html", all_items=session["all_items"], shopping_items=session["shopping_items"])


@app.route("/remove_items", methods=["POST"])
def remove_items():

    # get the items that where checked in the checkboxes
    checked_boxes = request.form.getlist("check")

    # Iterate over the the list of items which where checked in the checkboxes, find the right listindex and pop from list and update the session
    for item in checked_boxes:  
        if item in session["shopping_items"]:
            idx = session["shopping_items"].index(item)
            session["shopping_items"].pop(idx)
            session.modified = True
    return render_template("index.html", all_items=session["all_items"], shopping_items=session["shopping_items"])

@app.route("/groups")
def quote():
    return render_template("groups.html")


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        email = request.form.get("email")
        print("email:", type(email))
        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        #rows = db.execute("SELECT * FROM users WHERE email=:a", {"a": "q1"}) # returns a cursor
        rows = db.execute("SELECT * FROM users WHERE email = ?", (email,))
        print("rows", rows)
        
        username_search = db.fetchall() # is a list of tuples e.g. [(3, 'q1', 'q1', 'pbkdf2:sha')]
        #Accessing the 4 columns of the above list
        user_id_search = [x[0] for x in username_search][0]
        username_search_item = [x[1] for x in username_search][0]
        user_email_search = [x[2] for x in username_search][0]
        hash_search = [x[3] for x in username_search][0] 

        # Ensure username exists and password is correct
        if len(username_search) != 1 or not check_password_hash(hash_search, request.form.get("password")):
                print("check_password_hash:", check_password_hash(hash_search, request.form.get("password")))
                return apology("invalid username and/or password", 403)
        
        # Remember which user has logged in
        session["user_id"] = user_id_search

        # Remember username
        session["username"] = username_search_item
        username = session["username"]
        
        # Redirect user to home page
        flash(f"Hello {username} :)")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Logout Route
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash('logged out')
    return redirect(url_for("login"))

# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # if request method is post:
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation")

        # Ensure that Confirmed Password matches with Password
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("Confirmed Password does not match Password")

        # If all fields are filled out correctly...
        # Generate hash for password
        pw_hash = generate_password_hash(request.form.get("password"))
        # Add the users entry in database and add 10000 $ cash to the user
        try:
            db.execute("INSERT INTO users VALUES (null, ?,?,?)", (request.form.get("username"), request.form.get("email"), pw_hash))
            con.commit()
            con.close()
            flash('Sccessfully registered')
            return redirect("success")
        # If entry is not possible, because username is already in database return an apology

        except:
            return apology("Username already taken")
    # else user reached route via method "GET", then return register page
    else:
        return render_template("register.html")

@app.route("/success")
def success():
    return render_template("login.html")

# Code maybe needed later, otherwise delete (14.12.22)
'''
@app.route("/view", methods=["GET", "POST"])
def view():
    user = session["user"]
    print("user:", user)
    if request.method == "POST":
        for user in found_user:
            user.delete()

    else:
        print("view:", values)
        return render_template("view.html", values=values)

@app.route("/user", methods=["GET", "POST"])
def user():
    if "user" in session:
        user = session["user"]
        print(user)

        if request.method == "POST":
            print("post")
            email = request.form["email"]
            session['email'] = email
            found_user = user.query.filter_by(name=user).first()
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
'''

if __name__ == "__main__":
    app.run(debug=True)





