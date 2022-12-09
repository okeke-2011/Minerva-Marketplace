# import necessary libraries
import datetime
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy

# set up the app and database
app = Flask(__name__)
app.secret_key = "Minerva MarketPlace"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key = True)
    user_name = db.Column(db.String(100))
    user_email = db.Column(db.String(100))
    user_phone_no = db.Column(db.String(100))
    user_class = db.Column(db.String(100))
    user_about_me = db.Column(db.String(100))
    user_city = db.Column(db.String(100))
    user_pmoc = db.Column(db.String(100))
    user_oci = db.Column(db.String(100))
    user_profile_pic = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def __init__(self, name, password, email, phone, curr_class, city, about = "", pmoc = "", oci = "", pic = ""):
        self.user_name = name
        self.password = password
        self.user_email = email
        self.user_phone_no = phone
        self.user_class = curr_class
        self.user_about_me = about
        self.user_city = city
        self.user_pmoc = pmoc
        self.user_oci = oci
        self.user_profile_pic = pic

class Items(db.Model):
    item_id = db.Column(db.Integer, primary_key = True)
    requester_id = db.Column(db.Integer)
    poster_id = db.Column(db.Integer)
    item_status = db.Column(db.String(100))
    item_name = db.Column(db.String(100))
    item_location = db.Column(db.String(100))
    item_category = db.Column(db.String(100))
    item_description = db.Column(db.String(100))
    item_shelflife = db.Column(db.String(100))
    item_state = db.Column(db.String(100))
    date_posted = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    item_price = db.Column(db.String(100))
    item_pic = db.Column(db.String(100))

    def __init__(self, pos_id, name, loc, cat, state, descp="", shelf="", price="", pic="", req_id=-1, status="NR"):
        self.requester_id = req_id
        self.poster_id = pos_id
        self.item_status = status
        self.item_name = name
        self.item_location = loc
        self.item_category = cat
        self.item_description = descp
        self.item_shelflife = shelf
        self.item_state = state
        self.item_price = price
        self.item_pic = pic

# login page
@app.route("/", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        found_user = Users.query.filter_by(user_email = request.form["user_email"],password = request.form["password"]).first()
        if not found_user:
            flash(f"No profile for {request.form['user_email']}")
            return render_template("login.html")

        else:
            flash("Signed you in!")
            session["user_email"] = request.form["user_email"]
            session["password"] = request.form["password"]
            return redirect(url_for("all_items"))

    else:
        if "user_email" in session:
            flash("You're already logged in")
            return redirect(url_for("all_items"))
        else:
            return render_template("login.html")

@app.route("/sign_up", methods = ["POST", "GET"])
def sign_up():
    if request.method == "POST":
        err = False
        email, pw, conf_pw = request.form["user_email"], request.form["password"], request.form["conf_password"]
        
        found_user = Users.query.filter_by(user_email = email).first()
        if found_user:
            flash("This email already exists! Sign in instead")
            return redirect(url_for("login"))

        if "minerva.edu" not in email:
            flash("You need a minerva email to sign up!")
            err = True
        if len(pw) < 8:
            flash("Password needs to be at least 8 characters")
            err = True
        if pw != conf_pw:
            flash("Passwords don't match!")
            err = True

        if err:
            return render_template("sign_up.html")
        else:
            session["email"], session["pw"] = email, pw
            return redirect(url_for("create_user"))

    return render_template("sign_up.html")

@app.route("/all_items", methods = ["POST", "GET"])
def all_items():
    if "user_email" not in session:
        flash("You need to log in!")
        return redirect(url_for("login"))

    items = db.session.query(Items.item_id, Items.item_name, Items.item_price, Users.user_name).\
        join(Users, Users.user_id == Items.poster_id).\
        filter(Users.user_email != session["user_email"]).\
        filter(Items.item_status == "NR")

    if request.method == "POST":
        cats = [request.form[f"cat{i+1}"] for i in range(7) if f"cat{i+1}" in request.form]
        cities = [request.form[f"city{i+1}"] for i in range(8) if f"city{i+1}" in request.form]
        if "All" not in cats:
            items = items.filter(Items.item_category.in_(cats))
        if "All" not in cities:
            items = items.filter(Items.item_location.in_(cities))

        target_date = None
        if request.form["posted"] == "Past Day":
            target_date = datetime.datetime.now() - datetime.timedelta(days=1)
        elif request.form["posted"] == "Past Week":
            target_date = datetime.datetime.now() - datetime.timedelta(days=7)
        elif request.form["posted"] == "Past Month":
            target_date = datetime.datetime.now() - datetime.timedelta(days=30)
        elif request.form["posted"] == "Past Year":
            target_date = datetime.datetime.now() - datetime.timedelta(days=365)

        if target_date:
            items = items.filter(Items.date_posted >= target_date)

    ordered_items = items.order_by(Items.date_posted.desc()).all()
    return render_template("all_items.html", items=ordered_items)

@app.route("/my_items_post", methods = ["POST", "GET"])
def my_items_post():
    if "user_email" not in session:
        flash("You need to log in!")
        return redirect(url_for("login"))

    # database data to populate the tasks page
    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    items = db.session.query(Items.item_id, Items.item_name, Items.item_price, Items.item_status, Users.user_name).\
        join(Users, Users.user_id == Items.requester_id, isouter=True).\
        filter(Items.poster_id == user_id).\
        order_by(Items.date_posted.desc()).all()
    return render_template("my_items_post.html", items=items)

@app.route("/my_items_reqs", methods = ["POST", "GET"])
def my_items_reqs():
    if "user_email" not in session:
        flash("You need to log in!")
        return redirect(url_for("login"))

    # database data to populate the tasks page
    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    items = db.session.query(Items.item_id, Items.item_name, Items.item_price, Items.item_status, Users.user_name).\
        join(Users, Users.user_id == Items.poster_id, isouter=True).\
        filter(Items.requester_id == user_id).\
        order_by(Items.date_posted.desc()).all()
    return render_template("my_items_reqs.html", items=items)

@app.route("/create_user", methods = ["POST", "GET"])
def create_user():
    user = None
    if "user_email" in session:
        user = Users.query.filter_by(user_email=session["user_email"]).first()
        
    if request.method == "POST":
        required = ["name", "phone", "class", "city"]
        for field in required:
            if request.form.get(field, "") == "":   
                flash("Invalid submission! Fill out all starred fields")
                return render_template("create_user.html", user=user)
        if "user_email" not in session:
            new_usr = Users(name=request.form["name"],
                            password=session["pw"],
                            email=session["email"],
                            phone=request.form["phone"],
                            curr_class=request.form["class"],
                            city=request.form["city"],
                            about=request.form["about"],
                            pmoc=request.form["pmoc"],
                            oci=request.form["oci"])
            db.session.add(new_usr)
            db.session.commit()
            flash(f"Created profile for {session['email']}. Please sign in")
            return redirect(url_for("login"))
        else:
            usr = Users.query.filter_by(user_email=session["user_email"]).first()
            usr.user_name=request.form["name"]
            usr.user_phone_no=request.form["phone"]
            usr.user_class=request.form["class"]
            usr.user_city=request.form["city"]
            usr.user_about_me=request.form["about"]
            usr.user_pmoc=request.form["pmoc"]
            usr.user_oci=request.form["oci"]

            db.session.commit()
            flash(f"Edited profile for {session['email']}.")
            return redirect(url_for("user_info"))
    return render_template("create_user.html", user=user)

@app.route("/create_item", methods = ["POST", "GET"])
def create_item():
    if request.method == "POST":
        required = ["name", "price", "category", "city", "state"]
        for field in required:
            if request.form.get(field, "") == "":   
                flash("Invalid submission! Fill out all starred fields")
                return render_template("create_item.html")

        user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
        new_item = Items(pos_id = user_id, 
                        name=request.form["name"], 
                        loc=request.form["city"], 
                        cat=request.form["category"], 
                        state=request.form["state"], 
                        descp=request.form["descp"], 
                        shelf=request.form["shelf"], 
                        price=request.form["price"])
        db.session.add(new_item)
        db.session.commit()
        flash(f"Added new item '{request.form['name']}' for user '{session['user_email']}'")
        return redirect(url_for("my_items_post"))

    return render_template("create_item.html")

@app.route("/user_info", methods = ["POST", "GET"])
def user_info():
    if "user_email" in session:
        usr = Users.query.filter_by(user_email = session["user_email"], password = session["password"]).first()
        return render_template("user_info.html", usr=usr)
    else:
        flash("You need to log in!")
        return redirect(url_for("login"))

@app.route('/delete/item/<id>', methods=['GET', 'POST'])
def delete(id):
    item = db.session.query(Items).filter(Items.item_id==int(id)).first()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('my_items_post'))

@app.route('/req/item/<id>', methods=['GET', 'POST'])
def req(id):
    item = db.session.query(Items).filter(Items.item_id==int(id)).first()
    item.item_status = "R"
    item.requester_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    db.session.commit()
    return redirect(url_for('my_items_reqs'))

@app.route('/unreq/item/<id>', methods=['GET', 'POST'])
def unreq(id):
    item = db.session.query(Items).filter(Items.item_id==int(id)).first()
    item.item_status = "NR"
    item.requester_id = -1
    db.session.commit()
    return redirect(url_for('my_items_reqs'))

@app.route('/approve/item/<id>', methods=['GET', 'POST'])
def approve(id):
    item = db.session.query(Items).filter(Items.item_id==int(id)).first()
    item.item_status = "A"
    db.session.commit()
    return redirect(url_for('my_items_post'))

@app.route('/view/item/<id>', methods=['GET', 'POST'])
def view_item(id):
    item = db.session.query(*Items.__table__.columns).filter(Items.item_id==int(id)).first()
    buyer = db.session.query(*Users.__table__.columns).filter(Users.user_id==item.requester_id).first()
    seller = db.session.query(*Users.__table__.columns).filter(Users.user_id==item.poster_id).first()
    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    return render_template("view_item.html", item=item, buyer=buyer, seller=seller, user_id=user_id)

@app.route("/show_db")
def show_db():
    all_users = Users.query.all()
    all_tasks = Items.query.all()
    return render_template("show_db.html", all_users = all_users, all_tasks = all_tasks)

@app.route("/logout")
def logout():
    # delete all the session data
    if "user_email" in session:
        flash(f"Signed {session['user_email']} out")
        session.pop("user_email", None)
        session.pop("password", None)
    # send the user to the login page
    return redirect(url_for("login"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)