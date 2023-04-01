# import necessary libraries
import datetime
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import uuid
import boto3
from PIL import Image
from io import BytesIO  
import os

# set up the app and database
app = Flask(__name__)
app.secret_key = "Minerva MarketPlace"
app.config["UPLOAD_FOLDER"] = "static/images/"
# uncomment this line and comment the next for testing
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv('MAIL_USERNAME')
app.config["MAIL_PASSWORD"] = os.getenv('MAIL_PASSWORD')
app.config["MAIL_DEFAULT_SENDER"] = os.getenv('MAIL_DEFAULT_SENDER')
app.config["MAIL_SUPPRESS_SEND"] = False

db = SQLAlchemy(app)
mail = Mail(app)

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key = True)
    image_id = db.Column(db.Integer)
    user_name = db.Column(db.String(100))
    user_email = db.Column(db.String(100))
    user_phone_no = db.Column(db.String(100))
    user_class = db.Column(db.String(100))
    user_about_me = db.Column(db.String(100))
    user_city = db.Column(db.String(100))
    user_pmoc = db.Column(db.String(100))
    user_oci = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def __init__(self, name, password, email, phone, curr_class, city, pic_id, about = "", pmoc = "", oci = ""):
        self.user_name = name
        self.image_id = pic_id
        self.password = password
        self.user_email = email
        self.user_phone_no = phone
        self.user_class = curr_class
        self.user_about_me = about
        self.user_city = city
        self.user_pmoc = pmoc
        self.user_oci = oci

# clean up legacy code
class Items(db.Model):
    item_id = db.Column(db.Integer, primary_key = True)
    # requester_id = db.Column(db.Integer)
    poster_id = db.Column(db.Integer)
    image_id = db.Column(db.Integer)
    item_status = db.Column(db.String(100))
    item_name = db.Column(db.String(100))
    item_location = db.Column(db.String(100))
    item_category = db.Column(db.String(100))
    item_description = db.Column(db.String(100))
    item_shelflife = db.Column(db.String(100))
    item_state = db.Column(db.String(100))
    date_posted = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    item_price = db.Column(db.String(100))

    def __init__(self, pos_id, img_id, name, loc, cat, state, descp="", shelf="", price="", req_id=-1, status="NR"):
        # self.requester_id = req_id
        self.poster_id = pos_id
        self.image_id = img_id
        self.item_status = status
        self.item_name = name
        self.item_location = loc
        self.item_category = cat
        self.item_description = descp
        self.item_shelflife = shelf
        self.item_state = state
        self.item_price = price

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    bucket = db.Column(db.String(100))
    region = db.Column(db.String(100))

class Requests(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, primary_key=True)
    date_requested = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@app.route("/", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        found_user = Users.query.filter_by(user_email = request.form["user_email"],password = request.form["password"]).first()
        if not found_user:
            flash(f"Invalid credentials!")
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

@app.route("/forgot_password", methods = ["POST", "GET"])
def forgot_password():
    if request.method == "POST":
        found_user = Users.query.filter_by(user_email = request.form["user_email"]).first()
        if not found_user:
            flash("This email is not registered in our database!")
            return render_template("forgot_password.html")

        else:
            msg = Message("Forgot password", recipients=[found_user.user_email])
            msg.html = f"<p>Your Minerva Marketplace password is <b>{found_user.password}</b></p>"
            mail.send(msg)
            flash("Your password was sent to your email. You can use that to log in")
            return redirect(url_for("login"))


    return render_template("forgot_password.html")

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
    else:
        if "user_email" in session:
            flash("You're already logged in")
            return redirect(url_for("all_items"))

    return render_template("sign_up.html")

@app.route("/all_items", methods = ["POST", "GET"])
def all_items():
    if "user_email" not in session:
        flash("You need to log in!")
        return redirect(url_for("login"))

    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    requests_by_user = db.session.query(Requests).filter(Requests.requester_id == user_id)
    req_items = [req.item_id for req in requests_by_user]

    items = db.session.query(Items.item_id, Items.item_name, Items.item_price, Users.user_name,
                            Images.bucket, Images.filename, Images.region).\
        join(Users, Users.user_id == Items.poster_id).\
        join(Images, Images.id == Items.image_id).\
        join(Requests, Requests.item_id==Items.item_id, isouter=True).\
        filter(Users.user_email != session["user_email"]).\
        filter(Items.item_status != "A").\
        filter(Items.item_id.notin_(req_items))

    if request.method == "POST":
        cats = [request.form[f"cat{i+1}"] for i in range(6) if f"cat{i+1}" in request.form]
        cities = [request.form[f"city{i+1}"] for i in range(7) if f"city{i+1}" in request.form]
        if cats:
            items = items.filter(Items.item_category.in_(cats))
        if cities:
            items = items.filter(Items.item_location.in_(cities))
        if request.form["search"]:
            items = items.filter(or_(
                Items.item_name.ilike(f'%{request.form["search"]}%'), 
                Users.user_name.ilike(f'%{request.form["search"]}%')))

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
    seen_item_ids = set()
    final_items = []
    for item in ordered_items:
        if item.item_id not in seen_item_ids:
            seen_item_ids.add(item.item_id)
            num_reqs = len(db.session.query(Requests).filter(Requests.item_id==item.item_id).all()) 
            final_items.append((item, num_reqs))

    return render_template("all_items.html", items=final_items)

@app.route("/my_items_post", methods = ["POST", "GET"])
def my_items_post():
    if "user_email" not in session:
        flash("You need to log in!")
        return redirect(url_for("login"))

    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    all_statuses = db.session.query(Items.item_id, Items.item_name, Items.item_price, 
                                    Items.item_status, Images.bucket, Images.filename, 
                                    Images.region).\
        join(Images, Images.id == Items.image_id).\
        filter(Items.poster_id == user_id).\
        order_by(Items.date_posted.desc()).all()

    all_items = [("Not Requested", "grey", []), ("Requested", "orange", []), ("Approved", "green", [])]
    for item in all_statuses:
        if item.item_status == "NR":
            all_items[0][2].append(item)
        elif item.item_status == "R":
            num_reqs = len(db.session.query(Requests).filter(Requests.item_id==item.item_id).all()) 
            all_items[1][2].append((item, num_reqs))
        elif item.item_status == "A":
            all_items[2][2].append(item)

    return render_template("my_items_post.html", all_items=all_items)

@app.route("/my_items_reqs", methods = ["POST", "GET"])
def my_items_reqs():
    if "user_email" not in session:
        flash("You need to log in!")
        return redirect(url_for("login"))

    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    all_statuses = db.session.query(Items.item_id, Items.item_name, Items.item_price, 
                                    Items.item_status, Users.user_name,
                                    Images.bucket, Images.filename, Images.region).\
        join(Users, Users.user_id == Items.poster_id, isouter=True).\
        join(Images, Images.id == Items.image_id).\
        join(Requests, Requests.item_id==Items.item_id).\
        filter(Requests.requester_id == user_id).\
        order_by(Items.date_posted.desc()).all()

    all_items = [("Requested", "orange", []), ("Approved", "green", [])]
    for item in all_statuses:
        if item.item_status == "R":
            num_other_reqs = len(db.session.query(Requests).filter(Requests.item_id==item.item_id).all())-1
            all_items[0][2].append((item, num_other_reqs))
        elif item.item_status == "A":
            all_items[1][2].append(item)

    return render_template("my_items_reqs.html", all_items=all_items, user_id=user_id)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'png'}

@app.route("/create_user", methods = ["POST", "GET"])
def create_user():
    user = None
    no_name, no_phone, no_class, no_city, wrong_ext = False, False, False, False, False
    fields = ["name", "phone", "about", "class", "city", "pmoc", "oci"]
    prefilled = {field: "" for field in fields}
    if "user_email" in session:
        user = Users.query.filter_by(user_email=session["user_email"]).first()
        for field in fields:
            if field == "about":
                prefilled[field] = user.__getattribute__("user_about_me")
            elif field == "phone":
                prefilled[field] = user.__getattribute__("user_phone_no")
            else:
                prefilled[field] = user.__getattribute__(f"user_{field}")
    session["prefilled"] = prefilled
        
    if request.method == "POST":
        for field in fields:
            session["prefilled"][field] = request.form.get(field, "")

        if request.form.get("name", "") == "":
            no_name = True
        if request.form.get("phone", "") == "":
            no_phone = True
        if request.form.get("class", "") == "":
            no_class = True
        if request.form.get("city", "") == "":
            no_city = True

        if no_name or no_phone or no_class or no_city:
            flash("Invalid submission! Fill out all starred fields")
            return render_template("create_user.html", user=user,
                                    prefilled=session["prefilled"], no_name=no_name, 
                                    no_phone=no_phone, no_class=no_class, 
                                    no_city=no_city, wrong_ext=wrong_ext)

        if request.files["profile_pic"].filename:
            profile_pic = request.files["profile_pic"]
            if not allowed_file(profile_pic.filename):
                flash("FILE TYPE NOT ALLOWED! Only jpg or png files.")
                return render_template("create_user.html", user=user,
                                        prefilled=session["prefilled"], no_name=no_name, 
                                        no_phone=no_phone, no_class=no_class, 
                                        no_city=no_city, wrong_ext=True)

            new_filename = uuid.uuid4().hex + '.' + profile_pic.filename.rsplit('.', 1)[1].lower()
            bucket_name = "minerva-marketplace-pics"
            img = Images(original_filename=profile_pic.filename, filename=new_filename, 
                        bucket=bucket_name, region="us-west-2")
            
            db.session.add(img)
            db.session.commit()

            pic_id = img.id

            in_mem_file = BytesIO()
            resized_profile_pic = Image.open(profile_pic)
            resized_profile_pic.thumbnail((250, 250))
            resized_profile_pic.save(in_mem_file, format=resized_profile_pic.format)
            in_mem_file.seek(0)

            s3 = boto3.resource("s3")
            s3.Bucket(bucket_name).upload_fileobj(in_mem_file, new_filename)

        else:
            pic_id = -1

        if "user_email" not in session:
            new_usr = Users(name=request.form["name"],
                            password=session["pw"],
                            email=session["email"],
                            phone=request.form["phone"],
                            curr_class=request.form["class"],
                            city=request.form["city"],
                            about=request.form["about"],
                            pmoc=request.form["pmoc"],
                            oci=request.form["oci"],
                            pic_id=pic_id)
            db.session.add(new_usr)
            db.session.commit()
            flash(f"Created profile for {session['email']}. Please sign in")
            return redirect(url_for("login"))
        else:
            change = False
            usr = Users.query.filter_by(user_email=session["user_email"]).first()
            for field in fields:
                if field == "about":
                    if request.form[field] != usr.__getattribute__("user_about_me"):
                        usr.__setattr__("user_about_me", request.form[field])
                        change = True
                elif field == "phone":
                    if request.form[field] != usr.__getattribute__("user_phone_no"):
                        usr.__setattr__("user_phone_no", request.form[field])
                        change = True
                else:
                    if request.form[field] != usr.__getattribute__(f"user_{field}"):
                        usr.__setattr__(f"user_{field}", request.form[field])
                        change = True
            
            if pic_id != -1:
                usr.image_id = pic_id
                change = True

            if change:
                flash(f"Edited profile for {session['user_email']}")
                db.session.commit()

            return redirect(url_for("user_info"))
    return render_template("create_user.html", user=user,
                            prefilled=prefilled, no_name=no_name, 
                            no_phone=no_phone, no_class=no_class, 
                            no_city=no_city)

@app.route("/create_item", methods = ["POST", "GET"])
def create_item():
    no_name, no_price, no_category, no_city, no_state, no_image = False, False, False, False, False, False
    fields = ["name", "price", "description", "category", "city", "shelflife", "state"]
    session["prefilled_item"] = {field: "" for field in fields}
    
    if request.method == "POST":
        for field in fields:
            session["prefilled_item"][field] = request.form.get(field, "")

        if request.form.get("name", "") == "":
            no_name = True
        if request.form.get("price", "") == "":
            no_price = True
        if request.form.get("category", "") == "":
            no_category = True
        if request.form.get("city", "") == "":
            no_city = True
        if request.form.get("state", "") == "":
            no_state = True
        if not request.files["item_pic"].filename:
            no_image = True

        if no_name or no_price or no_category or no_city or no_state or no_image:
            flash("Invalid submission! Fill out all starred fields")
            return render_template("create_item.html", prefilled=session["prefilled_item"], 
                                    no_name=no_name, no_price=no_price, no_category=no_category,
                                    no_city=no_city, no_state=no_state, no_image=no_image)

        item_pic = request.files["item_pic"]
        if not allowed_file(item_pic.filename):
            flash("FILE TYPE NOT ALLOWED! Only jpg or png files.")
            return render_template("create_item.html", prefilled=session["prefilled_item"], 
                                    no_name=no_name, no_price=no_price, no_category=no_category,
                                    no_city=no_city, no_state=no_state, no_image=True)

        in_mem_file = BytesIO()
        resized_item_pic = Image.open(item_pic)
        resized_item_pic.thumbnail((250, 250))
        resized_item_pic.save(in_mem_file, format=resized_item_pic.format)
        in_mem_file.seek(0)

        new_filename = uuid.uuid4().hex + '.' + item_pic.filename.rsplit('.', 1)[1].lower()
        bucket_name = "minerva-marketplace-pics"
        s3 = boto3.resource("s3")
        s3.Bucket(bucket_name).upload_fileobj(in_mem_file, new_filename)

        img = Images(original_filename=item_pic.filename, filename=new_filename, 
                    bucket=bucket_name, region="us-west-2")
        
        db.session.add(img)
        db.session.commit()

        user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
        new_item = Items(pos_id = user_id, 
                        name=request.form["name"], 
                        loc=request.form["city"], 
                        cat=request.form["category"], 
                        state=request.form["state"], 
                        descp=request.form["description"], 
                        shelf=request.form["shelflife"], 
                        price=request.form["price"],
                        img_id=img.id)
        
        db.session.add(new_item)
        db.session.commit()
        flash(f"Added new item '{request.form['name']}' for user '{session['user_email']}'")
        session.pop("prefilled_item", None)
        return redirect(url_for("my_items_post"))

    return render_template("create_item.html", prefilled=session["prefilled_item"], 
                            no_name=no_name, no_price=no_price, no_category=no_category,
                            no_city=no_city, no_state=no_state)

@app.route("/user_info", methods = ["POST", "GET"])
def user_info():
    if "user_email" in session:
        usr = Users.query.filter_by(user_email=session["user_email"], password=session["password"]).first()
        img = Images.query.filter_by(id=usr.image_id).first()
        if img:
            image_link = f"https://{img.bucket}.s3.{img.region}.amazonaws.com/{img.filename}"
        else:
            image_link = "/static/male_avatar.png"
        return render_template("user_info.html", usr=usr, image_link=image_link)
    else:
        flash("You need to log in!")
        return redirect(url_for("login"))

@app.route('/delete/item/<id>', methods=['GET', 'POST'])
def delete(id):
    item = db.session.query(Items).filter(Items.item_id==int(id)).first()
    if item:
        db.session.query(Requests).filter(Requests.item_id==item.item_id).delete()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('my_items_post'))

@app.route('/req/item/<id>', methods=['GET', 'POST'])
def req(id):
    item = db.session.query(Items).filter(Items.item_id==int(id)).first()
    if item.item_status == "NR":
        item.item_status = "R"
    
    requester_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    request = Requests(item_id=item.item_id, requester_id=requester_id)

    db.session.add(request)
    db.session.commit()
    return redirect(url_for('my_items_reqs'))

@app.route('/unreq/item/<item_id>/<unreq_id>', methods=['GET', 'POST'])
def unreq(item_id, unreq_id):
    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    item = db.session.query(Items).filter(Items.item_id==int(item_id)).first()
    num_requesters = len(db.session.query(Requests).filter(Requests.item_id==int(item_id)).all()) - 1
    if num_requesters == 0:
        item.item_status = "NR"
    request = db.session.query(Requests).filter(
                    Requests.item_id==item.item_id, 
                    Requests.requester_id==unreq_id).first()
    db.session.delete(request)
    db.session.commit()

    if user_id != int(unreq_id):
        return redirect(url_for('view_item', item_id=item.item_id, buyer_num=0))
    return redirect(url_for('my_items_reqs'))

@app.route('/approve/item/<item_id>/<buyer_id>', methods=['GET', 'POST'])
def approve(item_id, buyer_id):
    item = db.session.query(Items).filter(Items.item_id==int(item_id)).first()
    if item:
        db.session.query(Requests).\
            filter(Requests.item_id==item.item_id).\
            filter(Requests.requester_id!=buyer_id).delete()
    item.item_status = "A"
    db.session.commit()
    return redirect(url_for('my_items_post'))

# test that people are ordered in the way they requested
@app.route('/view/item/<item_id>/<buyer_num>', methods=['GET', 'POST'])
def view_item(item_id, buyer_num):
    item = db.session.query(*Items.__table__.columns).filter(Items.item_id==int(item_id)).first()
    buyers = db.session.query(*Users.__table__.columns).\
                join(Requests, Requests.requester_id==Users.user_id).\
                filter(Requests.item_id==item.item_id).\
                order_by(Requests.date_requested.desc()).all()
    if buyers:
        buyer = buyers[int(buyer_num)]
    else:
        buyer = None
    
    seller = db.session.query(*Users.__table__.columns).filter(Users.user_id==item.poster_id).first()
    user_id = Users.query.filter_by(user_email=session["user_email"]).first().user_id
    request = db.session.query(Requests).filter(
                    Requests.item_id==item.item_id, 
                    Requests.requester_id==user_id).first()

    image = db.session.query(*Images.__table__.columns).filter(Images.id==item.image_id).first()
    image_link = f"https://{image.bucket}.s3.{image.region}.amazonaws.com/{image.filename}"

    if buyer and buyer.image_id != -1:
        buyer_pic = db.session.query(*Images.__table__.columns).filter(Images.id==buyer.image_id).first()
        buyer_pic_link = f"https://{buyer_pic.bucket}.s3.{buyer_pic.region}.amazonaws.com/{buyer_pic.filename}"
    else:
        buyer_pic_link = "/static/male_avatar.png"
    
    if seller and seller.image_id != -1:
        seller_pic = db.session.query(*Images.__table__.columns).filter(Images.id==seller.image_id).first()
        seller_pic_link = f"https://{seller_pic.bucket}.s3.{seller_pic.region}.amazonaws.com/{seller_pic.filename}"
    else:
        seller_pic_link = "/static/male_avatar.png"

    return render_template("view_item.html", item=item, buyer=buyer, len_buyers=len(buyers),
                            buyer_num=int(buyer_num), seller=seller, user_id=user_id, request=request, 
                            image_link=image_link, buyer_pic_link=buyer_pic_link, seller_pic_link=seller_pic_link)

@app.route("/show_db")
def show_db():
    all_users = Users.query.all()
    all_items = Items.query.all()
    all_images = Images.query.all()
    all_requests = Requests.query.all()
    return render_template("show_db.html", all_users=all_users, 
                            all_items=all_items, all_images=all_images,
                            all_requests=all_requests)

@app.route("/logout")
def logout():
    if "user_email" in session:
        flash(f"Signed {session['user_email']} out")
        session.pop("user_email", None)
        session.pop("password", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)