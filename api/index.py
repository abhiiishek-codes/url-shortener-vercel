from flask import Flask, request
from flask import render_template
import sqlite3
from flask import redirect
import random
import string
import qrcode

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("tmp/urls.db")
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS urls(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   code TEXT,
                   long_url TEXT,
                   clicks INTEGER DEFAULT 0)
                   """)
    conn.commit()
    conn.close()

def generate_code(length=5):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def code_exists(code):
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM urls WHERE code = ?",(code,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

BASE62 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def encode_base62(num):

    if num == 0:
        return BASE62[0]
    
    arr = []
    while(num != 0):
        rem = num % 62
        arr.append(BASE62[rem])
        num = num//62
    
    arr.reverse()

    return ''.join(arr)

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/shorten", methods=["POST"])
def shorten_url():
    long_url = request.form["url"]
    

    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO urls (long_url) VALUES (?)",(long_url,)
    )

    url_id = cursor.lastrowid
    code = encode_base62(url_id)

    cursor.execute(
        "UPDATE urls SET code = ? WHERE id = ?",(code,url_id)
    )
    conn.commit()
    conn.close()
    short_url = request.host_url + code

    img = qrcode.make(short_url)
    img.save(f"static/{code}.png")
    return render_template("index.html",short_url=short_url,qr_code=f"/static/{code}.png")

@app.route("/stats")
def stats():

    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    cursor.execute("SELECT code,long_url, clicks FROM urls")
    rows = cursor.fetchall()
    conn.close()
    return render_template("stats.html", rows=rows)

@app.route("/<code>")
def redirect_url(code):
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT long_url FROM urls WHERE code = ?",
        (code,)
    )
    result = cursor.fetchone()

    if result:

        cursor.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE code = ?",(code,)
            )
        conn.commit()    
        conn.close()
        return redirect(result[0])
    
    conn.close()
    return "URL not found"

init_db()