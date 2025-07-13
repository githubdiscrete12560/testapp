import os
import sys
import traceback
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Try importing Supabase with error handling
try:
    from supabase import create_client, Client
    print("✅ Supabase imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Supabase: {e}")
    sys.exit(1)

# Try importing dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ dotenv loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using environment variables directly")

app = Flask(__name__)

# Configuration with error checking
try:
    app.secret_key = os.getenv("SECRET_KEY")
    if not app.secret_key:
        print("❌ WARNING: SECRET_KEY not set!")
        app.secret_key = "fallback-secret-key-change-this"
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("❌ ERROR: SUPABASE_URL not set!")
        raise ValueError("Missing SUPABASE_URL environment variable")
    
    if not supabase_key:
        print("❌ ERROR: SUPABASE_KEY not set!")
        raise ValueError("Missing SUPABASE_KEY environment variable")
    
    print(f"✅ Environment variables loaded:")
    print(f"   SUPABASE_URL: {supabase_url[:20]}...")
    print(f"   SUPABASE_KEY: {supabase_key[:20]}...")
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client created successfully")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")
    supabase = None

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    try:
        print("🔄 Signup attempt started")
        
        # Check if Supabase is available
        if not supabase:
            print("❌ Supabase client not available")
            flash("Database connection error. Please try again later.", "danger")
            return redirect("/")
        
        # Get form data
        email = request.form.get("email")
        password = request.form.get("password")
        
        print(f"📧 Email: {email}")
        print(f"🔒 Password length: {len(password) if password else 0}")
        
        if not email or not password:
            print("❌ Missing email or password")
            flash("Email and password are required.", "danger")
            return redirect("/")
        
        # Hash the password
        print("🔄 Hashing password...")
        pw_hash = generate_password_hash(password)
        print("✅ Password hashed successfully")
        
        # Insert into Supabase
        print("🔄 Inserting user into database...")
        response = supabase.table("users").insert({
            "email": email,
            "password_hash": pw_hash
        }).execute()
        
        print(f"📊 Database response: {response}")
        
        # Check for errors in response
        if hasattr(response, 'error') and response.error:
            print(f"❌ Database error: {response.error}")
            if "duplicate key" in str(response.error).lower():
                flash("An account with this email already exists.", "warning")
            else:
                flash(f"Sign-up error: {response.error}", "danger")
            return redirect("/")
        
        # Check if we got data back
        if not response.data or len(response.data) == 0:
            print("❌ No data returned from database")
            flash("Account creation failed. Please try again.", "danger")
            return redirect("/")
        
        # Success case
        user_data = response.data[0]
        user_id = user_data.get("id")
        
        if not user_id:
            print("❌ No user ID in response")
            flash("Account creation failed. Please try again.", "danger")
            return redirect("/")
        
        print(f"✅ User created successfully with ID: {user_id}")
        
        # Set session
        session["user"] = user_id
        flash("Welcome! Your account has been created successfully.", "success")
        return redirect("/dashboard")
        
    except Exception as e:
        print(f"❌ Signup error: {e}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        flash("An unexpected error occurred during signup. Please try again.", "danger")
        return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    try:
        print("🔄 Login attempt started")
        
        if not supabase:
            print("❌ Supabase client not available")
            flash("Database connection error. Please try again later.", "danger")
            return redirect("/")
        
        email = request.form.get("email")
        password = request.form.get("password")
        
        print(f"📧 Login email: {email}")
        
        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect("/")
        
        # Fetch user
        print("🔄 Fetching user from database...")
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        print(f"📊 Login response: {response}")
        
        if not response.data:
            print("❌ No user found with this email")
            flash("No account found with that email.", "warning")
            return redirect("/")
        
        user = response.data[0]
        print(f"✅ User found: {user.get('id')}")
        
        # Verify password
        if not check_password_hash(user["password_hash"], password):
            print("❌ Password verification failed")
            flash("Incorrect password.", "danger")
            return redirect("/")
        
        print("✅ Login successful")
        session["user"] = user["id"]
        flash("Welcome back! You've been logged in successfully.", "success")
        return redirect("/dashboard")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        flash("An unexpected error occurred during login. Please try again.", "danger")
        return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect("/")
    
    user_id = session["user"]
    return f"Welcome to your dashboard! You're logged in as user ID {user_id}."

@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out successfully.", "info")
    return redirect("/")

@app.route('/favicon.ico')
def favicon():
    return '', 204

# Health check endpoint
@app.route('/health')
def health():
    status = {
        "status": "healthy",
        "supabase": "connected" if supabase else "disconnected",
        "environment_vars": {
            "SECRET_KEY": "set" if os.getenv("SECRET_KEY") else "missing",
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "missing",
            "SUPABASE_KEY": "set" if os.getenv("SUPABASE_KEY") else "missing"
        }
    }
    return status

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    print(f"❌ 500 Error: {error}")
    print(f"📍 Traceback: {traceback.format_exc()}")
    return "Internal Server Error - Check logs", 500

@app.errorhandler(404)
def not_found_error(error):
    return "Page not found", 404

if __name__ == "__main__":
    print("🚀 Starting Flask application...")
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)