from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "some-secret-key")

# --- Database setup ---
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["consent_data"]
users_coll = db["users"]
agreements_coll = db["agreements"]

# --- Auth helpers ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access that page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if "user_id" not in session:
        return None
    return users_coll.find_one({"_id": ObjectId(session["user_id"])})

# --- Authentication routes ---
@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if users_coll.find_one({"$or": [{"username": username}, {"email": email}]}):
            flash("Username or email already taken.", "danger")
            return redirect(url_for("register"))
        pwd_hash = generate_password_hash(password)
        result = users_coll.insert_one({
            "username": username,
            "email": email,
            "password_hash": pwd_hash,
            "created_at": datetime.utcnow()
        })
        session["user_id"] = str(result.inserted_id)
        flash("Registration successful. You are now logged in.", "success")
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["username_or_email"].strip()
        password = request.form["password"]
        user = users_coll.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email.lower()}
            ]
        })
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = str(user["_id"])
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next") or url_for("home")
            return redirect(next_page)
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/auth/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# --- Agreement routes ---
@app.route("/")
@login_required
def home():
    me = current_user()
    # show only agreements where I'm the target (party2)
    my_agreements = list(agreements_coll.find({"party2.user_id": me["_id"]})
                         .sort("created_at", -1))
    return render_template("home.html", agreements=my_agreements)

from bson import ObjectId

@app.route("/agreements/new/step1", methods=["GET", "POST"])
@login_required
def step1():
    if request.method == "POST":
        title = request.form["title"]
        party2_username = request.form["party2_username"].strip()

        target = users_coll.find_one({"username": party2_username})
        if not target:
            flash(f"No user found with username '{party2_username}'", "danger")
            return redirect(url_for("step1"))

        # session holds only strings
        session["agreement_data"] = {
            "title": title,
            "party1": {
                "user_id": session["user_id"],             # string
                "name": current_user()["username"]         # for display
            },
            "party2": {
                "user_id": str(target["_id"]),             # string
                "name": target["username"]                 # for display
            }
        }
        return redirect(url_for("step2"))
    return render_template("step1.html")


@app.route("/agreements/new/step2", methods=["GET", "POST"])
@login_required
def step2():
    if request.method == "POST":
        data = session["agreement_data"]
        # collect all the checkbox/radio inputs
        data["content"] = {
            "sexual_content": request.form.get("sexual_content"),
            "contraception": request.form.get("contraception"),
            "std_check": request.form.get("std_check"),
            "record_allowed": request.form.get("record_allowed")
        }
        session["agreement_data"] = data
        return redirect(url_for("signature_page"))
    return render_template("step2.html")

@app.route("/agreements/new/signature", methods=["GET", "POST"])
@login_required
def signature_page():
    if request.method == "POST":
        data = session.pop("agreement_data", {})

        # add the signature blob & timestamp
        data["signature"]    = request.form["signature_data"]
        data["created_at"]   = datetime.utcnow()

        # convert back to ObjectId for Mongo
        data["party1"]["user_id"] = ObjectId(data["party1"]["user_id"])
        data["party2"]["user_id"] = ObjectId(data["party2"]["user_id"])

        inserted = agreements_coll.insert_one(data)
        flash("Agreement created!", "success")
        return redirect(url_for("view_agreement", agreement_id=str(inserted.inserted_id)))

    return render_template("signature.html")

@app.route("/agreements/<agreement_id>")
@login_required
def view_agreement(agreement_id):
    agr = agreements_coll.find_one({"_id": ObjectId(agreement_id)})
    me = current_user()
    if not agr or agr["party2"]["user_id"] != me["_id"]:
        flash("You are not authorized to view that agreement.", "danger")
        return redirect(url_for("home"))
    return render_template("view_agreement.html", agreement=agr)

@app.route("/agreements/search", methods=["GET", "POST"])
@login_required
def search_agreements():
    me = current_user()
    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        # only search among agreements where I'm party2
        results = agreements_coll.find({
            "party2.user_id": me["_id"],
            "$or": [
                {"party1.username": {"$regex": keyword, "$options": "i"}},
                {"title": {"$regex": keyword, "$options": "i"}}
            ]
        })
        return render_template("search_results.html",
                               results=list(results),
                               keyword=keyword)
    return render_template("search.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
