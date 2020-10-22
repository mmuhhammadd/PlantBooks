import csv
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

f= open("books.csv")
reader = csv.reader(f)

for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (title, author, year, isbn) VALUES (:title, :author, :year, :isbn)", {"title": title, "author": author, "year": year, "isbn": isbn})
    print(f"added {title} by {author}")
db.commit()