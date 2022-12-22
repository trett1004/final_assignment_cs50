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

# To check the taken route


# Create a function that returns all grocery-entries from database
def get_db():
    db.execute("select name from groceries WHERE group_id = ?", (session["enter_group"],))
    all_data = db.fetchall()
    all_data = [str(val[0]) for val in all_data]
    # make a copy of the list which contains only the first database entry
    shopping_list = all_data.copy() 
    return all_data, shopping_list

# Make the function like above only with autocomplete
def autocomplete():
    db.execute("select name from groceries WHERE group_id = ? and name LIKE ?", (session["enter_group"], request.args.get("q"),))
    print("autocomp session enter_group:", session["enter_group"])
    data = db.fetchall()
    data = [str(val[0]) for val in data]
    print("data:", data)
    # make a copy of the list which contains only the first database entry

    return data


# Create a function that returns all group-entries from database
def get_groups():
    db.execute("select group_name from groupmembers WHERE user_id = ?", (session["user_id"],))
    all_groups = db.fetchall()
    all_groups = [str(val[0]) for val in all_groups]
    return all_groups
    
def group_members():
    group_name_list = []
    list_group_name_list = []
    #print("@ groupmembers session groups:", session["groups"])
    for i in range(len(session["groups"])):
        db.execute("select username from groupmembers WHERE group_name = ?", (session["groups"][i],))
        #print("@ groupmembers session groups[i]:", session["groups"][i])
        user_name = db.fetchall()
        #print("@ groupmembers user_name:", user_name)
        for j in range(len(user_name)):
            user_name_item = [x[0] for x in user_name][j]
            #print("@ groupmembers user_name_item:", user_name_item)
            group_name_list.append(user_name_item)
            #print("@ groupmembers group_name_list:", group_name_list)
        list_group_name_list.append(group_name_list)  
        #print("@ groupmembers list_group_name_list:", list_group_name_list) 
        session["list_group_name_list"] = list_group_name_list
        #print("@ groupmembers session list_group_name_list:", session["list_group_name_list"]) 
        group_name_list = []
        #print("@ groupmembers session groups:", session["groups"])
    return session["list_group_name_list"]




# In the index route it is possible to add and remove items. The further routes (see routes below) "/add_items" and "/remove_items" return index.html
@app.route("/", methods=["GET", "POST"])
def home():
    rule = request.url_rule
    # store the two lists in session so the other routes can access them
    if '/login' in rule.rule:
        return render_template("index.html")
    else:
        try:
            session["all_items"], session["shopping_items"] = get_db()
            return render_template("index.html", all_items=session["all_items"], shopping_items=session["shopping_items"])
        except:
            return render_template("index.html")

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

@app.route("/search", methods=["GET"])
def search_items():
# Search the entries (items) that are stored for the group in the database
    #search = request.args.get("q") 
    search = request.args.get("q", "")   
    #db.execute("select name from groceries WHERE group_id = ? AND name LIKE ?", (session["enter_group"], '%'+ search + '%'))
    print("route search_items q:", search)
    print("route search_items session enter_group:", session["enter_group"])
    data = db.fetchall()
    data = [str(val[0]) for val in data]
    print("route seacht_items data:", data)
    
    return render_template("search.html", data=data)
    #"%" + request.args.get("q") + "%",)
    #items = autocomplete()
    #return render_template("index_test.html", items=items)

# Shows the current groups of the user and has a "create new group" function
@app.route("/groups", methods=["GET", "POST"])
def groups():
   
    #store the groupnames in a session
    session["groups"] = get_groups()
    if request.method == "POST":
        
        # group_name_list = []
        new_group = request.form.get("create_group")
        db.execute("INSERT INTO groups(group_name) VALUES (?)", (new_group,))
        #print("@goups post new_group:", new_group)
        # Get the all data to make db entry in table "groupmembers"
        # From table "groups" get the group_id
        new_group_id = db.execute("SELECT group_id FROM groups WHERE group_name = ?", (new_group,))
        new_group_id = db.fetchall()
        new_group_id = [x[0] for x in new_group_id][0]

        # Insert group data and user data into table "groupmembers"
        db.execute("INSERT INTO groupmembers(group_id, group_name, user_id, username) VALUES (?,?,?,?)", (new_group_id, new_group, session["user_id"], session["username"]))
        con.commit()
        session["groups"] = get_groups() # Update the session
        
        session["list_group_name_list"] = group_members()
        print("@goups post session groups:", session["groups"])
        print("@goups post session list_group_name_list:", session["list_group_name_list"])
        flash(f"Group *{new_group}* created:)")

        return render_template("groups.html", groups=session["groups"], list_group_name_list=session["list_group_name_list"])

    else:
        # If user does not have any groups
        if not session["groups"]:
            flash(f"You don't have any groups yet :)")
            return render_template("groups.html")
        # If user has groups display them
        else: 
            group_name_list = []
            list_group_name_list = []
            for i in range(len(session["groups"])):
                db.execute("select username from groupmembers WHERE group_name = ?", (session["groups"][i],))
                user_name = db.fetchall()
                for j in range(len(user_name)):
                    user_name_item = [x[0] for x in user_name][j]
                    group_name_list.append(user_name_item)
                list_group_name_list.append(group_name_list)   
                session["list_group_name_list"] = list_group_name_list
                group_name_list = []
            return render_template("groups.html", groups=session["groups"], list_group_name_list=session["list_group_name_list"])

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    # Add another user to table groupmembers
    if request.method == "POST":
    # Get all the needed variables for make insert in database    
        # Get the Groupname from form
        group_name = request.form.get("select_groups")
        # print("@ add_user group_name:", group_name)
        #Get the corresponding group_id from selected group_name from table groups
        db.execute("SELECT group_id FROM groups WHERE group_name = ?", (group_name,))
        group_id = db.fetchall()
        group_id = [x[0] for x in group_id][0]
        # Get the user_id and user_name 
        user_name = request.form.get("add_user")
        #print("@ add_user user_name:", user_name)
        # Get the corresponding user_id from database
        try:
            rows = db.execute("SELECT user_id FROM users WHERE username = ?", (user_name,))
            user_id = db.fetchall()
            user_id = [x[0] for x in user_id][0]

            # Insert data into table groupmembers
            db.execute("INSERT INTO groupmembers(group_id, group_name, user_id, username) VALUES (?,?,?,?)", (group_id, group_name, user_id, user_name))
            con.commit()
        except:
            return apology("User does not exist")
        flash(f"You added {user_name} to group {group_name} :)")
        session["list_group_name_list"] = group_members()
        return render_template("groups.html", groups=session["groups"], list_group_name_list=session["list_group_name_list"])
    else:
        return render_template("groups.html", groups=session["groups"]) 

@app.route("/remove_yourself", methods=["GET", "POST"])
def remove_yourself():
    #session["groups"] = get_groups()
    # Remove yourself from a group
    if request.method == "POST":
        removal_group_name = request.form.get("select_removal_group")
        db.execute("DELETE FROM groupmembers WHERE group_name = ? and user_id = ?", (removal_group_name, session["user_id"]))
        con.commit()
        flash(f"You removed yourself from Group *{removal_group_name}* :)")
        return render_template("groups.html", groups=session["groups"])
    else:
        return render_template("groups.html", groups=session["groups"]) 

@app.route("/enter_group", methods=["GET", "POST"])
def enter_group():

    # Enter a group and display only the groceries that have the corresponding group_id in table groceries
    if request.method == "POST":
        enter_group = request.form.get("enter_group")
        db.execute("SELECT group_id FROM groups WHERE group_name = ?", (enter_group,))
        enter_group = db.fetchall()
        enter_group = [val[0] for val in enter_group][0]
        session["enter_group"] = enter_group

        if enter_group:
            session["all_items"], session["shopping_items"] = get_db()
            return render_template("index.html", all_items=session["all_items"], shopping_items=session["shopping_items"])
    else:
        return render_template("groups.html", groups=session["groups"], list_group_name_list=session["list_group_name_list"])

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        email = request.form.get("email")
        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = ?", (email,))
        
        username_search = db.fetchall() # is a list of tuples e.g. [(3, 'q1', 'q1', 'pbkdf2:sha')]
        #Accessing the 4 columns of the above list
        user_id_search = [x[0] for x in username_search][0]
        username_search_item = [x[1] for x in username_search][0]
        user_email_search = [x[2] for x in username_search][0]
        hash_search = [x[3] for x in username_search][0] 

        # Ensure username exists and password is correct
        if len(username_search) != 1 or not check_password_hash(hash_search, request.form.get("password")):
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
    if request.method == "POST":
        for user in found_user:
            user.delete()

    else:
        return render_template("view.html", values=values)

@app.route("/user", methods=["GET", "POST"])
def user():
    if "user" in session:
        user = session["user"]

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





