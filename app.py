from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "some-secret-key"

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["consent_data"]
collection = db["agreements"]
@app.route("/")
def home():
    all_record = list(collection.find().sort("created_at", -1))
    return render_template("home.html", agreements = all_record)
# @app.route("/agreements/new", methods=["GET","POST"])
# def create_new():
#     if request.method == "POST":
#         title = request.form.get("title")
#         party1_name = request.form.get("party1_name")
#         party1_id = request.form.get("party1_id")
#         party2_name = request.form.get("party2_name")
#         party2_id = request.form.get("party2_id")
#         content = request.form.get("content")
#         signature_type = "text"
#         signature_data = request.form.get("signature_data")
#         new_agree = {
#             "title": title,
#             "party1": {
#                 "name": party1_name,
#                 "id_number": party1_id
#             },
#             "party2": {
#                 "name": party2_name,
#                 "id_number": party2_id
#             },
#             "content": content,
#             "signature": {
#                 "method": signature_type,
#                 "data": signature_data
#             },
#             "created_at": datetime.now()
#         }
#         collection.insert_one(new_agree)
#         return redirect(url_for("home"))
#     else:
#         return render_template("new_agreement.html")
@app.route("/agreements/new/step1", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        title = request.form.get("title")
        party1_name = request.form.get("party1_name")
        party1_id = request.form.get("party1_id")
        party2_name = request.form.get("party2_name")
        party2_id = request.form.get("party2_id")
        session["agreement_data"] = {
            "title": title,
            "party1": {
                "name": party1_name,
                "id_number": party1_id
            },
            "party2": {
                "name": party2_name,
                "id_number": party2_id
            }
        }
        
        return redirect(url_for("step2"))
    else:
        return render_template("step1.html")

@app.route("/agreements/new/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        agreement_data = session.get("agreement_data", {})

        sexual_content = request.form.get("sexual_content")  
        contraception = request.form.get("contraception")   
        std_check = request.form.get("std_check") 
        record_allowed = request.form.get("record_allowed") 
        agreement_data["content"] = {
            "sexual_content": sexual_content,
            "contraception": contraception,
            "std_check": std_check,
            "record_allowed": record_allowed
        }
        session["agreement_data"] = agreement_data
        
        return redirect(url_for("signature_page"))
    else:
        return render_template("step2.html")

@app.route("/agreements/new/signature", methods=["GET", "POST"])
def signature_page():
    if request.method == "POST":
        agreement_data = session.get("agreement_data", {})
        signature_base64 = request.form.get("signature_data")

        agreement_data["signature"] = signature_base64
        agreement_data["created_at"] = datetime.now()

        session["agreement_data"] = agreement_data
        
        inserted_id = collection.insert_one(agreement_data).inserted_id
        session.pop("agreement_data", None)
        return redirect(url_for("view_agreement", agreement_id=str(inserted_id)))
    else:
        return render_template("signature.html")

@app.route("/agreements/<agreement_id>")
def view_agreement(agreement_id):
    from bson.objectid import ObjectId
    agreement = collection.find_one({"_id": ObjectId(agreement_id)})
    return render_template("view_agreement.html", agreement=agreement)

@app.route("/agreements/search", methods=["GET", "POST"])
def search_agreements():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        results = collection.find({
            "$or": [
                {"party1.name": {"$regex": keyword, "$options": "i"}},
                {"party2.name": {"$regex": keyword, "$options": "i"}}
            ]
        })
        return render_template("search_results.html", results=results, keyword=keyword)
    else:
        return render_template("search.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
        