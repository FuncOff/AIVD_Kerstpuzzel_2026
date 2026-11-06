from flask import Flask, request, jsonify, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder=".", static_url_path="")

# 1. Database initialiseren
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Bestaande tabel voor scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deelnemers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT UNIQUE NOT NULL,
            score INTEGER NOT NULL
        )
    """)
    
    # Nieuwe tabel voor gebruikersaccounts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gebruikers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruikersnaam TEXT UNIQUE NOT NULL,
            wachtwoord_hash TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# --- Pagina Routes ---
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/userForm.html")
def user_form():
    return app.send_static_file("userForm.html")

@app.route("/login.html")
def login_page():
    return app.send_static_file("login.html")

@app.route("/signup.html")
def signup_page():
    return app.send_static_file("signup.html")


# --- API Endpoints voor Deelnemers/Scores ---
@app.route("/api/deelnemers", methods=["GET"])
def get_deelnemers():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT naam, score FROM deelnemers ORDER BY score DESC")
    rows = cursor.fetchall()
    conn.close()
    
    resultaat = [{"naam": row[0], "score": row[1]} for row in rows]
    return jsonify(resultaat)

@app.route("/api/deelnemers", methods=["POST"])
def add_or_update_deelnemer():
    data = request.json
    naam = data.get("naam")
    score = data.get("score")

    if not naam or score is None:
        return jsonify({"error": "Ongeldige invoer"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO deelnemers (naam, score) VALUES (?, ?)
        ON CONFLICT(naam) DO UPDATE SET score=excluded.score
    """, (naam, score))
    conn.commit()
    conn.close()
    return jsonify({"message": "Succesvol opgeslagen"}), 200


# --- API Endpoints voor Authenticatie (Aanmelden & Inloggen) ---
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    gebruikersnaam = data.get("gebruikersnaam")
    wachtwoord = data.get("wachtwoord")

    if not gebruikersnaam or not wachtwoord:
        return jsonify({"error": "Vul alle velden in"}), 400

    hashed_pw = generate_password_hash(wachtwoord)

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO gebruikers (gebruikersnaam, wachtwoord_hash) VALUES (?, ?)", 
                       (gebruikersnaam, hashed_pw))
        conn.commit()
        conn.close()
        return jsonify({"message": "Account succesvol aangemaakt"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Gebruikersnaam bestaat al"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    gebruikersnaam = data.get("gebruikersnaam")
    wachtwoord = data.get("wachtwoord")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT wachtwoord_hash FROM gebruikers WHERE gebruikersnaam = ?", (gebruikersnaam,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row[0], wachtwoord):
        return jsonify({"message": "Inloggen gelukt"}), 200
    else:
        return jsonify({"error": "Ongeldige gebruikersnaam of wachtwoord"}), 401


if __name__ == "__main__":
    app.run(debug=True, port=5000)