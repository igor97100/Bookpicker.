import os

from flask import Flask, session, render_template, request, redirect, url_for, g
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=['POST','GET'])
def register():
    if request.method == 'POST':
        try:
            password = request.form.get("password")
            email = request.form.get("email")
            name = request.form.get("name")
        except ValueError:
            return render_template("error.html", message="Please fill the Email and Password")

        if db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).rowcount != 0:
            return render_template("error.html", message="This email is allready registered")

        db.execute("INSERT INTO users (email, name, password) VALUES (:email, :name, :pass)",
                {"email": email, "name":name, "pass": password})
        db.commit()

        return render_template("success.html")
    return render_template("register.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)
        try:
            password = request.form.get("password")
            email = request.form.get("email")
        except ValueError:
            return render_template("error.html", message="Please fill the Email and Password")
        if db.execute("SELECT * FROM users WHERE email = :email and password = :pass", {"email": email, "pass": password}).rowcount == 0:
            return render_template("error.html", message="Wrond username or password")
        else:
            user_id= db.execute("SELECT id FROM users WHERE email = :email and password = :pass", {"email": email, "pass": password}).fetchone()
            session['user_id'] = user_id
            return redirect(url_for('search'))

    return render_template("login.html")

@app.before_request
def before_request():
    g.user_id = None
    if 'user_id' in session:
        g.user_id = session['user_id']


@app.route("/home",methods= ['POST','GET'])
def search():
    if g.user_id:
        if request.method == 'POST':
            search_key = request.form.get("search_key")
            search_key = '%'+search_key+'%'
            books = db.execute("SELECT * FROM books where (isbn LIKE :search_key) or (title LIKE :search_key) or (author LIKE :search_key)",{"search_key":search_key}).fetchall()

            return render_template("search_results.html",books=books)
        return render_template("search.html")
    return "log in first"

@app.route("/<string:isbn>")
def book(isbn):
    return render_template("book.html" , isbn=isbn)
