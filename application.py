import os
import requests
from flask import Flask, session, render_template, flash, request, redirect, url_for, jsonify, abort
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



@app.route("/", methods=["POST", "GET"])
def signin():
    session["names"] = []
    names = session["names"]

    names = session.get("names", None)
    if request.method == "POST":
        names.clear()
    if request.method == "GET":
        names.clear()
    return render_template("signin.html")

@app.route("/verifysignin", methods=["POST"])
def verifysignin():

    username = request.form.get("username")
    password = request.form.get("password")

    names = session["names"]

    if request.method == "POST":
        names.append(username)

    if username == '':
        flash('Enter username and password!')
        return redirect(url_for('signin'))
    if password == '':
        flash('Enter username and password!')
        return redirect(url_for('signin'))
    if db.execute("SELECT*FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount != 0:
        return redirect(url_for('home'))
    else:
        flash('Invaild username or password!')
        return redirect(url_for('signin'))

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/verifysignup", methods=["POST"])
def verifysignup():
    username = request.form.get("username")
    password = request.form.get("password")
    repassword = request.form.get("repassword")

    if username == '':
        flash('Enter your username and password!')
        return redirect(url_for('signup'))
    if password == '':
        flash('Enter your username and password!')
        return redirect(url_for('signup'))
    if password != repassword:
        flash('Password does not match!')
        return redirect(url_for('signup'))

    
    if db.execute("SELECT*FROM users WHERE username = :username", {"username": username}).rowcount == 1:
        flash('Account already exists!')
        return redirect(url_for('signup'))
    else:
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
        db.commit()
        flash('Signed Up successfully!')
        return redirect(url_for('signin'))


@app.route("/Home")
def home():
    names = session.get("names", None)
    if not names:
        return render_template("error.html")
    else:
        name = names[0]
        books = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 25").fetchall()

        return render_template("home.html", name=name, books=books)

@app.route("/search", methods=["POST", "GET"])
def search():
    names = session.get("names", None)
    if not names:
        return render_template("error.html")
    else:
        key = request.form.get("search")
        if key == '':
            results = 0
        else:
            results = db.execute("SELECT*FROM books WHERE title LIKE '%"+key+"%' OR author LIKE '%"+key+"%' OR isbn LIKE '%"+key+"%' OR year LIKE '%"+key+"%'").fetchall()
            
        return render_template("result.html", results=results, key=key)

@app.route("/book")
def book():
    names = session.get("names", None)
    if not names:
        return render_template("error.html")
    else:
        isbn = request.args.get("isbn")
        book = db.execute("SELECT*FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        bookid = book.id

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "iujw9GWRVRE8eUQyP6Q80g", "isbns": isbn})
        data = res.json()

        avr = data["books"][0]["average_rating"]
        wrc = data["books"][0]["work_ratings_count"]

        reviews = db.execute("SELECT*FROM reviews WHERE bookid = :bookid", {"bookid": bookid}).fetchall()

        return render_template("book.html",  book=book, avr=avr, wrc=wrc, reviews = reviews)

@app.route("/addreview", methods=["POST"])
def addreview():
    names = session.get("names", None)
    if not names:
        return render_template("error.html")
    else:
        isbn = request.args.get("isbn")

        names = session.get("names", None)
        username = names[0]

        book = db.execute("SELECT*FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        bookid = book.id

        review = request.form.get("review")
        rating = request.form.get("rating")

        if rating == None:
            flash('Please add rating!')
            return redirect(url_for('book', isbn=isbn))

        if review == "":
            flash('Please add review!')
            return redirect(url_for('book', isbn=isbn))
        
        if db.execute("SELECT*FROM reviews WHERE username = :username AND bookid = :bookid", {"username": username, "bookid": bookid}).rowcount == 1:
            flash('You already reviewed this book!')
            return redirect(url_for('book', isbn=isbn))
        else:
            db.execute("INSERT INTO reviews (review, rating, username, bookid) VALUES (:review, :rating, :username, :bookid)", {"review": review, "rating": rating, "username": username, "bookid": bookid})
            db.commit()
            return redirect(url_for('book', isbn=isbn))

@app.route("/book/api/<string:isbn>")
def bookapi(isbn):
    names = session.get("names", None)
    if not names:
        return render_template("error.html")
    else:
        if db.execute("SELECT*FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount != 1:
            abort(404)
        else:
            book = db.execute("SELECT*FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
            title = book.title
            author = book.author
            year = book.year
            isbn = book.isbn
            bookid = book.id
            reviewcount = db.execute("SELECT review FROM reviews WHERE bookid = :bookid", {"bookid": bookid}).rowcount
            averagerating = db.execute("SELECT AVG(rating) FROM reviews WHERE bookid = :bookid", {"bookid": bookid}).fetchone()[0]

            return jsonify ({
                "title": title,
                "author": author,
                "year": year,
                "isbn": isbn,
                "review_count": reviewcount,
                "average_rating": averagerating
            })

 




    