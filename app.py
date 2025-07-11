import os
from flask import Flask, render_template, request, redirect, session, flash
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["email"]
    password = request.form["password"]

    # Hash the password
    pw_hash = generate_password_hash(password)

    # Insert into Supabase
    data, error = supabase.table("users").insert({
        "email": email,
        "password_hash": pw_hash
    }).execute()

    if error:
        flash(f"Sign-up error: {error.message}", "danger")
        return redirect("/")
    session["user"] = data[0]["id"]
    return redirect("/dashboard")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    # Fetch user
    resp = supabase.table("users").select("*").eq("email", email).execute()
    users = resp.data

    if not users:
        flash("No account found with that email.", "warning")
        return redirect("/")
    user = users[0]

    # Verify password
    if not check_password_hash(user["password_hash"], password):
        flash("Incorrect password.", "danger")
        return redirect("/")

    session["user"] = user["id"]
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return f"?? Welcome! You’re logged in as user ID {session['user']}."

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
