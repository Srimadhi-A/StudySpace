from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_mail import Mail, Message
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
import os
from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import random
from datetime import datetime
from flask import request, session, make_response
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import qrcode
import re

#app = Flask(__name__)
app = Flask(__name__, template_folder='templates')

app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studyspace.db'
db = SQLAlchemy(app)


# Database Path
DB_PATH = os.path.join(app.instance_path, "studyspace.db")
os.makedirs(app.instance_path, exist_ok=True)  # Ensure instance folder exists

# Uploads folder setup
UPLOAD_FOLDER = "static/uploads/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Ensure the receipts directory exists
os.makedirs("receipts", exist_ok=True)
# Flask-Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'studyspace796@gmail.com'        # ✅ Your email
app.config['MAIL_PASSWORD'] = 'ygnm xvzk rtxf yqcl'           # ✅ App password (not your Gmail password)

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)
def get_user_by_email(email):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    con.close()
    return user

# Function to get DB connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Function to check file extensions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_pic TEXT DEFAULT 'default.png'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_cost INTEGER NOT NULL,
            course_duration TEXT NOT NULL
        )
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    course_name TEXT NOT NULL,
    date_earned TEXT NOT NULL
);
""")
     # ✅ Insert courses only if they don’t exist
    courses = [
        ("Python Basics", 699, "4 Weeks"),
        ("Web Development", 299, "3 Weeks"),
        ("Cybersecurity Basics", 799, "4 Weeks"),
        ("Machine Learning", 999, "6 Weeks"),
        ("Artificial Intelligence Basics", 899, "4 Weeks"),
        ("Cloud Computing Basics", 999, "4 Weeks"),
        ("C Programming", 699, "3 Weeks"),
        ("C++ Programming", 699, "3 Weeks"),
        ("DevOps", 799, "3 Weeks"),
        ("Data Science Essentials", 249, "4 Weeks"),
        ("Deep Learning", 199, "1 Week"),
        ("Digital Marketing", 199, "1 Week"),
        ("Data Structures",249,"4 Weeks"),
        ("Data Matrix",249,"4 Weeks"),
        ("Data Analysis",299,"4 Weeks"),
        ("Chemistry",299,"4 Weeks"),
        ("Data Manipulation", 599, "4 Weeks"),
        ("Physics Fundamentals", 599, "4 Weeks")
    ]

    for course in courses:
        cursor.execute("SELECT * FROM courses WHERE course_name = ?", (course[0],))
        if cursor.fetchone() is None:  # ✅ Check if course already exists
            cursor.execute("INSERT INTO courses (course_name, course_cost, course_duration) VALUES (?, ?, ?)", course)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            course_cost INTEGER NOT NULL,
            course_duration TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            module_name TEXT NOT NULL,
            module_description TEXT,
            video_url TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
    """)
    
    cursor.execute("SELECT id, username, course_name, course_cost FROM enrollments")
    enrollments = cursor.fetchall()

    # Calculate total revenue
    cursor.execute("SELECT SUM(course_cost) FROM enrollments")
    total_revenue = cursor.fetchone()[0] or 0  # Ensure it doesn't return None
    
    conn.commit()
    conn.close()
            
# First Page
@app.route("/")
def logo():
    return render_template("logo.html")
#Home page
@app.route("/home")
def home():
    return render_template("home/index.html")  # Explicitly mention the subfolder
# signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # ✅ Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("signup"))
        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.", "danger")
            return redirect(url_for("signup"))
        if not re.search(r"[a-z]", password):
            flash("Password must contain at least one lowercase letter.", "danger")
            return redirect(url_for("signup"))
        if not re.search(r"[0-9]", password):
            flash("Password must contain at least one number.", "danger")
            return redirect(url_for("signup"))
        # Optional: Special character check
        # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        #     flash("Password must contain at least one special character.", "danger")
        #     return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)  # 👈 Hash after validation

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, hashed_password))
            conn.commit()
            flash("Signup successful! Please login.", "success")
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists!", "danger")
            conn.close()
            return redirect(url_for("signup"))

    return render_template("signup.html")



ADMIN_EMAIL = "studyspace796@gmail.com"
ADMIN_PASSWORD = "1234"  # Store securely in production

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True, default="default.jpg")  # Default profile pic
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)  # Relationship

# Course Model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    # description = db.Column(db.Text, nullable=False)
    # instructor = db.Column(db.String(100), nullable=False)
    modules = db.relationship('CourseModule', backref='course', lazy=True)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)  # Relationship

# Course Module Model
class CourseModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    module_number = db.Column(db.Integer, nullable=False)
    module_title = db.Column(db.String(200), nullable=False)
    video_url = db.Column(db.String(300), nullable=False)

# Enrollment Model
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']

        if user_type == "admin":
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                session['admin'] = email
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid Admin Credentials!', 'danger')
                return redirect(url_for('login'))
        else:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session["username"] = user["username"]  # ✅ Store username in session
                session["user_id"] = user["id"]  # ✅ Store user ID for future reference
                return redirect(url_for('home'))  # ✅ Redirect to profile
            else:
                flash('Invalid Student Credentials!', 'danger')

    return render_template('login.html')


# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()

    # ✅ Fetch actual user data instead of just count
    users = conn.execute('SELECT * FROM users').fetchall()  
    courses = conn.execute('SELECT * FROM courses').fetchall()
    enrollments = conn.execute('SELECT * FROM enrollments').fetchall()
    
    # Calculate total revenue
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(course_cost) FROM enrollments")
    total_revenue = cursor.fetchone()[0] or 0  # Ensure it doesn't return None
    cursor.execute("""
    SELECT course_name, COUNT(*) as enrollments
    FROM enrollments
    GROUP BY course_name
    ORDER BY enrollments DESC
    LIMIT 5
""")
    top_courses = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users, courses=courses, enrollments=enrollments, total_revenue=total_revenue, top_courses=top_courses)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        if user:
            token = s.dumps(email, salt='email-reset')
            link = url_for('reset_password', token=token, _external=True)
            print(f'Reset Link: {link}')
            msg = Message('Password Reset for StudySpace',
                          sender='studyspace796@gmail.com',  # ✅ Make sure email is correct
                          recipients=[email])
            msg.body = f'Click the link to reset your password: {link}'
            mail.send(msg)
            flash('Reset link sent to your email.', 'success')
        else:
            flash('Email not registered.', 'danger')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-reset', max_age=3600)
    except SignatureExpired:
        flash("The reset link has expired.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password)

        con = sqlite3.connect('instance/studyspace.db')
        cur = con.cursor()
        cur.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
        con.commit()
        con.close()

        flash('Password updated successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

# Courses Page
@app.route("/courses")
def courses():
    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return render_template("course.html", courses=courses)

# Python course
@app.route("/python")
def python():
    course_id = 1  # Assuming Python course has ID 1 in your database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("python.html", course=course, enrolled=enrolled)

# Python courses
@app.route("/pycourse")
def pycourse():
    course_id = 1  # Python course ID
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("pycourse.html", modules=modules)

# Web development course
@app.route("/web_development")
def web_development():
    course_id = 2  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("web development.html", course=course, enrolled=enrolled)

@app.route("/webcourse")
def webcourse():
    course_id = 2 
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("webcourse.html", modules=modules)

# Cyber Security course
@app.route("/cybersecurity")
def cybersecurity():
    course_id = 3  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("cybersecurity.html", course=course, enrolled=enrolled)
@app.route("/cybercourse")
def cybercourse():
    course_id = 3  # Cybersecurity course ID
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("cybercourse.html", modules=modules)


# Machine Learning course
@app.route("/machinelearning")
def machinelearning():
    course_id = 4  
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()
    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())
    conn.close()
    return render_template("machinelearning.html", course=course, enrolled=enrolled)

@app.route("/machinecourse")
def machinecourse():
    course_id = 4  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("machinecourse.html", modules=modules)


# Artifical Intelligence course
@app.route("/artificial")
def artificial():
    course_id = 5  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("artificial.html", course=course, enrolled=enrolled)

@app.route("/artificialcourse")
def artificialcourse():
    course_id = 5  # Cybersecurity course ID
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("artificialcourse.html", modules=modules)

# Cloud Computing course
@app.route("/cloudcomputing")
def cloudcomputing():
    course_id = 6  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("cloudcomputing.html", course=course, enrolled=enrolled)

@app.route("/cloudcourse")
def cloudcourse():
    course_id = 6  # Cybersecurity course ID
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()
    conn.close()
    return render_template("cloudcourse.html", modules=modules)

# C course
@app.route("/cprogram")
def cprogram():
    course_id = 7 
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("C Programming.html", course=course, enrolled=enrolled)


@app.route("/cprogramcourse")
def cprogramcourse():
    course_id = 7    # Cybersecurity course ID
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("cprogramcourse.html", modules=modules)

# C plus
@app.route("/cplus , endpoint='cplus'")
def cplus():
    course_id = 8 
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()
    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())
    conn.close()
    return render_template("cplus.html", course=course, enrolled=enrolled)

@app.route("/cpluscourse")
def cpluscourse():
    course_id = 9    # Cybersecurity course ID
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()
    conn.close()
    return render_template("cpluscourse.html", modules=modules)

# Devops
@app.route("/devops")
def devops():
    course_id = 9 
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()
    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
        cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
        enrolled = bool(cursor.fetchone())
    conn.close()
    return render_template("devops.html", course=course, enrolled=enrolled)

@app.route("/devopscourse")
def devopscourse():
    course_id = 9    # Cybersecurity course ID
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course modules or content for cybersecurity
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()
    conn.close()
    return render_template("devopscourse.html", modules=modules)

#quiz
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')  # Create a quiz.html file in templates folder

#data manipulation
@app.route('/data_manipulation')
def data_manipulation():
    course_id = 17  # Assuming Data Manipulation course has ID 11 in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()
    # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())
    conn.close()
    return render_template("data manipulation.html", course=course, enrolled=enrolled)

# Data manipulation courses
@app.route("/dmcourse")
def dmcourse():
    course_id = 17  
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()
    conn.close()
    return render_template("dmcourse.html", modules=modules)

#physics
@app.route('/Physics')
def Physics():
    course_id = 18 
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("physics.html", course=course, enrolled=enrolled)
@app.route("/physicscourse")
def physicscourse():
    course_id = 18   
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("physicscourse.html", modules=modules)

#deeplearing
@app.route('/digitalmarketing')
def digitalmarketing():
    course_id = 12  # Assuming Data Manipulation course has ID 11 in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("digitalmarketing.html", course=course, enrolled=enrolled)
        
# digital marketing courses
@app.route("/digitalcourse")
def digitalcourse():
    course_id = 12   
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("digitalcourse.html", modules=modules)

#data science
@app.route('/datascience')
def datascience():
    course_id = 10  # Assuming Data Manipulation course has ID 11 in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("datascience.html", course=course, enrolled=enrolled)

        
# Data science courses
@app.route("/dscourse")
def dscourse():
    course_id = 10  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("dscourse.html", modules=modules)


#deeplearing
@app.route('/deeplearning')
def deeplearning():
    course_id = 11  # Assuming Data Manipulation course has ID 11 in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("deeplearning.html", course=course, enrolled=enrolled)

@app.route("/dlcourse")
def dlcourse():
    course_id = 11  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("dlcourse.html", modules=modules)
#data strutucre
@app.route('/datastructure')
def datastructure():
    course_id = 13  # Assuming Data Manipulation course has ID 11 in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("datastructure.html", course=course, enrolled=enrolled)
        
# Data structure courses
@app.route("/datastructurecourse")
def datastructurecourse():
    course_id = 13  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("datastructurecourse.html", modules=modules)

#data martix
@app.route('/datamatrix')
def datamatrix():
    course_id = 14  # Assuming Data Manipulation course has ID 11 in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("datamatrix.html", course=course, enrolled=enrolled)
        
# Data matrix courses
@app.route("/datamatrixcourse")
def datamatrixcourse():
    course_id = 14  
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("datamatrixcourse.html", modules=modules)
#data analysis
@app.route('/data_analysis')
def data_analysis():
    course_id = 15  
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("data_analysis.html", course=course, enrolled=enrolled)
        
# Data analysis courses
@app.route("/data_analysiscourse")
def data_analysiscourse():
    course_id = 15 
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("data_analysiscourse.html", modules=modules)

#chemistry
@app.route('/Chemistry')
def Chemistry():
    course_id = 16  
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    course = cursor.fetchone()

        # Check if the user is enrolled
    enrolled = False
    if "username" in session:
            cursor.execute("SELECT * FROM enrollments WHERE username = ? AND course_id = ?", (session["username"], course_id))
            enrolled = bool(cursor.fetchone())

    conn.close()
    return render_template("chemistry.html", course=course, enrolled=enrolled)
        
# chemistry courses
@app.route("/Chemistrycourse")
def Chemistrycourse():
    course_id = 16
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch course modules or content
    cursor.execute("SELECT * FROM course_modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()
    return render_template("Chemistrycourse.html", modules=modules)

@app.route('/course/<course_name>')
def course_content(course_name):
    course_templates = {
        "Python": "pycourse.html",
        "Data Manipulation and Cleaning": "dmcourse.html",
        "Web Development": "webcourse.html",
        "Machine Learning": "machinecourse.html",
        "Cybersecurity Basics": "cybercourse.html",
        "Artificial Intelligence Basics" : "artificialcourse.html",
        "Cloud Computing Basics": "cloudcourse.html",
        "C Programming": "cprogramcourse.html",
        "Data Science Essentials": "dscourse.html",
        "Deep Learning": "dlcourse.html",
        "Digital Marketing": "digitalcourse.html",
        "C++ Programming": "cpluscourse.html",
        "DevOps": "devopscourse.html",
        "Data Structures": "datastructurecourse.html",
        "Data Matrix": "datamatrixcourse.html",
        "Chemistry": "Chemistrycourse.html",
        "Physics Fundamentals": "physicscourse.html",
        "Data Analysis": "data_analysiscourse.html"
    }

    # Get the template file name based on course_name
    template_file = course_templates.get(course_name)

    if template_file:
        return render_template(template_file)
    else:
        return render_template("404.html"), 404  # Handle invalid course name
    
@app.route('/enroll', methods=['POST', 'GET'])
def enroll():
    if "username" not in session:
        flash("You must be logged in to enroll!", "warning")
        return redirect(url_for("login"))

    username = session["username"]

    # 🔹 Fetch course details from POST form or GET URL parameters
    if request.method == 'POST':
        course_id = request.form.get('course_id', "").strip()
        course_name = request.form.get('course_name', "Unknown Course").strip()
        course_cost = request.form.get('course_cost', "0").strip()
        course_duration = request.form.get('course_duration', "Unknown Duration").strip()
    else:
        course_id = request.args.get('course_id', "").strip()
        course_name = request.args.get('course_name', "Unknown Course").strip()
        course_cost = request.args.get('course_cost', "0").strip()
        course_duration = request.args.get('course_duration', "Unknown Duration").strip()

    # 🔹 Validate `course_id`
    if not course_id.isdigit():
        flash("Invalid course ID!", "danger")
        return redirect(url_for("courses"))

    course_id = int(course_id)  # Convert to integer

    # 🔹 Validate `course_cost`
    try:
        course_cost = int(course_cost)
    except ValueError:
        flash("Invalid course cost!", "danger")
        return redirect(url_for("courses"))

    # 🔹 Database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user is already enrolled
    cursor.execute("SELECT 1 FROM enrollments WHERE username = ? AND course_id = ?", (username, course_id))
    already_enrolled = cursor.fetchone()

    if already_enrolled:
        flash(f"You are already enrolled in {course_name}!", "info")
    else:
        cursor.execute("""
            INSERT INTO enrollments (username, course_id, course_name, course_cost, course_duration) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, course_id, course_name, course_cost, course_duration))
        conn.commit()
        flash(f"Successfully enrolled in {course_name}!", "success")

    conn.close()

    # 🔹 Redirect Logic
    if course_cost > 0:
        return redirect(url_for('payment', 
                                course_id=course_id, 
                                course_name=course_name, 
                                course_cost=course_cost, 
                                course_duration=course_duration))
    else:
        return redirect(url_for('data_manipulation' if course_id == 10 else 'courses'))  # Adjust based on your logic
    
@app.route('/certificate', methods=["GET"])
def certificate():
    username = session.get("username")

    if not username:
        return "User not logged in.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the latest enrolled course for the user
    cursor.execute("""
        SELECT course_name 
        FROM enrollments 
        WHERE username = ? 
        LIMIT 1
    """, (username,))
    
    course_data = cursor.fetchone()
    conn.close()

    if not course_data:
        return "No course found for this user.", 400

    course_name = course_data["course_name"]  
    completion_date = datetime.now().strftime("%Y-%m-%d")  

    # Save the certificate in the database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO certificates (username, course_name, date_earned)
        VALUES (?, ?, ?)
    """, (username, course_name, completion_date))

    conn.commit()
    conn.close()

    return render_template('certificate.html', 
                           username=username, 
                           course_name=course_name, 
                           completion_date=completion_date) 

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if "username" not in session:
        flash("You must be logged in to continue!", "warning")
        return redirect(url_for("login"))

    course_id = request.args.get('course_id')
    course_name = request.args.get('course_name', "Unknown Course")
    course_cost = request.args.get('course_cost', "0")
    course_duration = request.args.get('course_duration', "Unknown Duration")

    if request.method == 'POST':
        # Assuming payment is successful, redirect to invoice
        return redirect(url_for('invoice',
                                course_id=course_id,
                                course_name=course_name,
                                course_cost=course_cost,
                                course_duration=course_duration))

    return render_template('payment.html', 
                           course_id=course_id, 
                           course_name=course_name, 
                           course_cost=course_cost, 
                           course_duration=course_duration)

@app.route('/confirm_payment', methods=["GET"])
def confirm_payment():
    # Get data from query parameters
    course_name = request.args.get('course_name')  
    course_cost = request.args.get('course_cost')
    course_duration = request.args.get('course_duration')
    course_id = request.args.get('course_id')

    # Ensure user is logged in
    username = session.get("username")
    if not username:
        flash("Please log in to view your payment confirmation.", "warning")
        return redirect(url_for("login"))

    # Fetch the enrolled course details securely
    conn = None
    enrolled_course = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM enrollments 
            WHERE username = ? AND course_id = ?
        """, (username, course_id))
        enrolled_course = cursor.fetchone()
    except Exception as e:
        flash("An error occurred while retrieving your enrollment details.", "danger")
        print("Database Error:", str(e))
    finally:
        if conn:
            conn.close()

    if not enrolled_course:
        flash("Enrollment not found! Please check your courses.", "danger")
        return redirect(url_for("courses"))

    return render_template('payment_confirmation.html', 
                           course_name=course_name, 
                           course_cost=course_cost, 
                           course_duration=course_duration,
                           course_id=course_id,
                           enrolled_course=enrolled_course)

# Payment Process
@app.route('/process_payment', methods=['POST'])
def process_payment():
    course_name = request.form.get('course_name')
    course_cost = request.form.get('course_cost')
    course_duration = request.form.get('course_duration')
    course_id = request.form.get('course_id')
    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')

    # Validate Card Number (Should be 12-16 digits)
    if not card_number.isdigit() or len(card_number) < 12 or len(card_number) > 16:
        return "Invalid Card Number! Please enter a valid 12-16 digit card number."

    # Validate CVV (Should be 3 digits)
    if not cvv.isdigit() or len(cvv) != 3:
        return "Invalid CVV! Please enter a valid 3-digit CVV."

    # Validate Expiry Date (Should be MM/YY and between 2025-2045)
    try:
        exp_month, exp_year = expiry_date.split('/')
        exp_month = int(exp_month)
        exp_year = int("20" + exp_year)  # Convert YY to YYYY

        if exp_month < 1 or exp_month > 12:
            return "Invalid Expiry Date! Month must be between 01 and 12."

        if exp_year < 2025 or exp_year > 2045:
            return "Invalid Expiry Year! Must be between 2025 and 2045."

    except:
        return "Invalid Expiry Date format! Use MM/YY format."

    # ✅ Pass data using query parameters
    return redirect(url_for('confirm_payment', 
                            course_name=course_name, 
                            course_cost=course_cost, 
                            course_duration=course_duration,
                            course_id=course_id))

#invoice
@app.route('/download_invoice/<int:course_id>')
def download_invoice(course_id):
    course_name = request.args.get('course_name', 'Unknown Course')
    course_cost = request.args.get('course_cost', '0')
    course_duration = request.args.get('course_duration', 'Unknown Duration')
    purchase_date = request.args.get('purchase_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    username = session.get("username")

    if course_name == "Unknown Course" or course_cost == "0":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_name, course_cost, course_duration FROM enrollments WHERE username = ? AND course_id = ?", (username, course_id))
        course_data = cursor.fetchone()
        conn.close()
        if course_data:
            course_name, course_cost, course_duration = course_data

    if course_name == "Unknown Course":
        course_name = "Course Name Not Available"

    invoice_id = f"INV{random.randint(1000, 9999)}"

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    def center_text(text, y, font="Helvetica", size=12, bold=False, color=colors.black):
        if bold:
            pdf.setFont("Helvetica-Bold", size)
        else:
            pdf.setFont(font, size)
        pdf.setFillColor(color)
        text_width = pdf.stringWidth(text, font, size)
        x = (width - text_width) / 2
        pdf.drawString(x, y, text)

    base_y = height - 50

    # 🧑 Name and Title
    center_text("STUDY SPACE", base_y, size=20, bold=True, color=colors.darkred)
    base_y -= 20
    center_text(username, base_y, size=14, bold=True, color=colors.darkred)
    base_y -= 18
    center_text("Your Learning Partner", base_y, size=12, color=colors.grey)
    base_y -= 22
    center_text("INVOICE", base_y, size=16, bold=True)
    base_y -= 16
    center_text(f"Invoice ID: {invoice_id}   |   Date: {purchase_date[:10]}", base_y, size=10)
    base_y -= 40

    # 📄 Course Info
    line_gap = 24
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, base_y, f"Username: {username}")
    base_y -= line_gap
    pdf.drawString(100, base_y, f"Course Name: {course_name}")
    base_y -= line_gap
    pdf.drawString(100, base_y, f"Course Duration: {course_duration}")
    base_y -= line_gap
    pdf.drawString(100, base_y, f"Course Cost: ₹{course_cost}")
    base_y -= line_gap
    pdf.drawString(100, base_y, f"Purchase Date: {purchase_date}")
    base_y -= line_gap + 10

        # 📎 QR Code - Enlarged and Right Aligned
    qr_data = f"Invoice ID: {invoice_id}\nUser: {username}\nCourse: {course_name}\nCost: ₹{course_cost}\nDate: {purchase_date}\nThank you for choosing Study Space!"
    qr = qrcode.make(qr_data)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_image = ImageReader(qr_buffer)

    # Bigger size
    qr_width = 160
    qr_height = 160

    # Right-aligned with 50pt margin
    qr_x = width - qr_width - 50
    qr_y = base_y - qr_height + 60  # Moves QR code 60 points higher


    pdf.drawImage(qr_image, qr_x, qr_y, width=qr_width, height=qr_height)

    # Leave space below QR
    base_y = qr_y - 40



    # Footer separator
    pdf.setStrokeColor(colors.black)
    pdf.line(100, base_y, 500, base_y)
    base_y -= 20

    # Footer Text
    center_text("Thank you for learning with us!", base_y, font="Helvetica-Oblique", size=11)
    base_y -= 15
    center_text("For any queries, contact: studyspace796@gmail.com", base_y, size=10)
    base_y -= 20
    center_text("STUDY SPACE · Learn Grow Succeed", base_y, bold=True, size=10)
    base_y -= 30

    # 🆘 Student Support Info Section
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(100, base_y, "Student Support Info:")

    pdf.setFont("Helvetica", 10)
    support_details = [
        "📧 Email: studyspace@796.com",
        "🌐 Website: www.studyspace.com",
        "📱 WhatsApp: +91-9876543210",
        "🕘 Support Hours: Mon - Fri, 10:00 AM to 6:00 PM"
    ]
    for info in support_details:
        base_y -= 15
        pdf.drawString(110, base_y, info)

    base_y -= 30  # space before Notes Section

    # 📝 Notes Section
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(100, base_y, "Notes:")

    pdf.setFont("Helvetica", 10)
    notes = [
        "1. This invoice is generated for your course purchase.",
        "2. In case of any dispute, please contact us within 7 days.",
        "3. All courses come with lifetime access once purchased.",
        "4. No refunds after course completion."
    ]
    for note in notes:
        base_y -= 15
        pdf.drawString(110, base_y, note)

    base_y -= 30  # space before signature

    # Signature
    pdf.drawString(400, base_y, "Authorized Signature")
    pdf.line(390, base_y - 2, 500, base_y - 2)

    pdf.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{username}_{course_id}.pdf'
    return response


@app.route('/profile')
def profile():
    if "username" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))
    
    username = session["username"]  # Get the username from session

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch user data
    user_data = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    # Fetch enrolled courses
    enrollments = cursor.execute("SELECT * FROM enrollments WHERE username = ?", (username,)).fetchall()
    
    # Fetch earned certificates
    certificates = cursor.execute("SELECT course_name, date_earned FROM certificates WHERE username = ?", (username,)).fetchall()

    conn.close()
    unique_certificates = []
    seen_courses = set()

    for cert in certificates:
        if cert['course_name'] not in seen_courses:
            seen_courses.add(cert['course_name'])
            unique_certificates.append(cert)
    if not user_data:
        flash("User not found!", "danger")
        return redirect(url_for("login"))
    
    return render_template('profile.html', user=user_data, enrollments=enrollments,certificates=unique_certificates)
# Upload Profile Picture Route
@app.route("/upload_profile_pic", methods=["POST"])
def upload_profile_pic():
    if "username" not in session:
        flash("You must be logged in!", "danger")
        return redirect(url_for("login"))

    if "profile_pic" not in request.files:
        flash("No file uploaded!", "warning")
        return redirect(url_for("profile"))

    file = request.files["profile_pic"]
    if file.filename == "":
        flash("No selected file!", "warning")
        return redirect(url_for("profile"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Update database with new profile picture
        username = session["username"]
        conn = get_db_connection()
        conn.execute("UPDATE users SET profile_pic = ? WHERE username = ?", (filename, username))
        conn.commit()
        conn.close()

        flash("Profile picture updated!", "success")
    else:
        flash("Invalid file type!", "danger")

    return redirect(url_for("profile"))
# Edit Profile Route
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "username" not in session:
        flash("You must be logged in!", "danger")
        return redirect(url_for("login"))
    username = session["username"]
    conn = get_db_connection()
    user_data = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if request.method == "POST":
        new_username = request.form["username"]
        new_email = request.form["email"]

        conn.execute("UPDATE users SET username = ?, email = ? WHERE username = ?", 
                     (new_username, new_email, username))
        conn.commit()
        conn.close()

        # Update session with new username
        session["username"] = new_username
        session["email"] = new_email

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    conn.close()
    return render_template("edit_profile.html", user=user_data)

@app.route("/htmldebugging")
def htmldebugging():
    return render_template("htmldebugging.html")
@app.route("/jsdebugging")
def jsdebugging():
    return render_template("jsdebugging.html")

#Game
@app.route("/game")
def game():
    username = session.get("username", "guest")  # Adjust this based on your login logic
    return render_template("game.html", username=username)


#cyber
@app.route('/cyber')
def cyber():
    if 'username' in session:
        return render_template('cyber.html', username=session['username'])
    return redirect(url_for('login'))


#memory
@app.route('/memory')
def memory():
    if 'username' in session:
        return render_template('memorycard.html', username=session['username'])
    return redirect(url_for('login'))

#word
@app.route('/word')
def word():
    if 'username' in session:
        return render_template('word.html', username=session['username'])
    return redirect(url_for('login'))
#tech
@app.route('/tech')
def tech():
    return render_template('tech.html')
#maths
@app.route('/maths')
def maths():
    return render_template('maths.html')
#fraction
@app.route('/fraction')
def fraction():
    return render_template('frac.html')
#chemistry
@app.route('/chemistry')
def chemistry():
    return render_template('che.html')
#grammar
@app.route('/grammar')
def grammar():
    return render_template('grammar.html')
#vocubalary
@app.route('/vocubalary')
def vocubalary():
    return render_template('vol.html')

# Contact Page
@app.route("/contact")
def contact():
    return render_template("contact.html")

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# Run the App
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
