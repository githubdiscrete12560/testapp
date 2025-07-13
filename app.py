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
        # Error case - handle different types of errors
        if "duplicate key" in str(error).lower() or "already exists" in str(error).lower():
            flash("An account with this email already exists. Please try logging in instead.", "warning")
        else:
            flash(f"Sign-up error: {error.message}", "danger")
        return redirect("/")
    else:
        # Success case - user created successfully
        user_id = data[0]["id"]
        user_email = data[0]["email"]
        
        # Set user session
        session["user"] = user_id
        
        # Success message
        flash(f"Welcome! Your account has been created successfully.", "success")
        
        return redirect("/dashboard")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    # Fetch user
    resp = supabase.table("users").select("*").eq("email", email).execute()
    users = resp.data

    if not users:
        # No user found with this email
        flash("No account found with that email. Please check your email or sign up.", "warning")
        return redirect("/")
    else:
        # User found - check password
        user = users[0]

        if not check_password_hash(user["password_hash"], password):
            # Incorrect password
            flash("Incorrect password. Please try again.", "danger")
            return redirect("/")
        else:
            # Login successful
            session["user"] = user["id"]
            flash(f"Welcome back! You've been logged in successfully.", "success")
            return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect("/")
    else:
        # User is logged in
        user_id = session["user"]
        return f"Welcome to your dashboard! You're logged in as user ID {user_id}."

@app.route("/logout")
def logout():
    if "user" in session:
        flash("You've been logged out successfully.", "info")
        session.clear()
    else:
        flash("You weren't logged in.", "info")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)