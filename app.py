from flask import Flask, request, jsonify, render_template
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder=".", static_url_path="")

# Initialise Database
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Table for scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deelnemers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT UNIQUE NOT NULL,
            score INTEGER NOT NULL
        )
    """)
    
    # Table for users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gebruikers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruikersnaam TEXT UNIQUE NOT NULL,
            wachtwoord_hash TEXT NOT NULL
        )
    """)

    # Table for puzzles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gebruiker_puzzels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            puzzel_nr INTEGER NOT NULL,
            UNIQUE(naam, puzzel_nr)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# Page Routes
@app.route("/")
def leaderboard():
    return app.send_static_file("leaderboard.html")

@app.route("/questions.html")
def questions():
    return app.send_static_file("questions.html")

@app.route("/userForm.html")
def user_form():
    return app.send_static_file("userForm.html")

@app.route("/login.html")
def login_page():
    return app.send_static_file("login.html")

@app.route("/signup.html")
def signup_page():
    return app.send_static_file("signup.html")

@app.route("/easteregg.html")
def valsspeler_page():
    return app.send_static_file("easteregg.html")


# API endpoints
@app.route("/api/deelnemers", methods=["GET"])
def get_deelnemers():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # We get the name and scores from the participants
    cursor.execute("SELECT naam, score FROM deelnemers")
    rows = cursor.fetchall()
    
    resultaat = []
    for row in rows:
        naam = row[0]
        score = row[1]
        
        # Count how many puzzles a user has completed for the tiebreaker
        cursor.execute("SELECT COUNT(*) FROM gebruiker_puzzels WHERE naam = ?", (naam,))
        aantal_opgelost = cursor.fetchone()[0]
        
        resultaat.append({
            "naam": naam,
            "score": score,             # Total amount of points
            "opgelost": aantal_opgelost # Total amount of completed puzzles
        })
        
    conn.close()
    
    # Sort results with flasks
    resultaat.sort(key=lambda x: (x["score"], x["opgelost"]), reverse=True)
    
    return jsonify(resultaat)

@app.route("/api/deelnemers", methods=["POST"])
def add_or_update_deelnemer():
    data = request.json
    naam = data.get("naam")
    puzzels = data.get("puzzels", []) # List of completed puzzles

    if not naam:
        return jsonify({"error": "Ongeldige invoer"}), 400

    # Loads puzzles out of the json files
    try:
        with open("puzzels.json", "r", encoding="utf-8") as f:
            puzzels_lijst = json.load(f)
    except FileNotFoundError:
        puzzels_lijst = []

    # Make a dictionary of puzzle_number->points
    punten_map = {p["nummer"]: p.get("punten", 1) for p in puzzels_lijst}

    # Get total score from checked puzzles
    score = sum(punten_map.get(p_nr, 1) for p_nr in puzzels)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Update total scores in participant tables
    cursor.execute("""
        INSERT INTO deelnemers (naam, score) VALUES (?, ?)
        ON CONFLICT(naam) DO UPDATE SET score=excluded.score
    """, (naam, score))
    
    # Delete old checks and load new ones
    cursor.execute("DELETE FROM gebruiker_puzzels WHERE naam = ?", (naam,))
    for p_nr in puzzels:
        cursor.execute("INSERT OR IGNORE INTO gebruiker_puzzels (naam, puzzel_nr) VALUES (?, ?)", (naam, p_nr))
        
    conn.commit()
    conn.close()
    return jsonify({"message": "Succesvol opgeslagen"}), 200

# Endpoint to load completed puzzles of a participant
@app.route("/api/gebruiker-puzzels/<naam>", methods=["GET"])
def get_gebruiker_puzzels(naam):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT puzzel_nr FROM gebruiker_puzzels WHERE naam = ?", (naam,))
    rows = cursor.fetchall()
    conn.close()
    
    puzzels = [row[0] for row in rows]
    return jsonify(puzzels)

# Endpoint to get which participant did which question
@app.route("/api/questions", methods=["GET"])
def get_questions():
    try:
        with open("puzzels.json", "r", encoding="utf-8") as f:
            puzzels_lijst = json.load(f)
    except FileNotFoundError:
        puzzels_lijst = []

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Count the total unique participants for the percentage
    cursor.execute("SELECT COUNT(DISTINCT gebruikersnaam) FROM gebruikers")
    totaal_row = cursor.fetchone()
    totaal_gebruikers = totaal_row[0] if totaal_row and totaal_row[0] > 0 else 1
    
    resultaat = []
    
    for p in puzzels_lijst:
        p_nr = p["nummer"]
        p_naam = p.get("naam", f"Puzzel {p_nr}")
        p_punten = p.get("punten", 1)  # Get the points from the json file
        
        # Get the names of completors for this specific puzzle
        cursor.execute("SELECT naam FROM gebruiker_puzzels WHERE puzzel_nr = ?", (p_nr,))
        rows = cursor.fetchall()
        namen = [row[0] for row in rows]
        
        aantal = len(namen)
        percentage = round((aantal / totaal_gebruikers) * 100, 1)
        
        resultaat.append({
            "nummer": p_nr,
            "number": p_naam,
            "punten": p_punten,
            "aantal": aantal,
            "percentage": percentage,
            "people": ", ".join(namen) if namen else "Nog door niemand opgelost"
        })
        
    conn.close()
    
    # Sort on amount of completions
    # After on points
    resultaat.sort(key=lambda x: (-x["aantal"], x["punten"]))
    
    return jsonify(resultaat)

# Enpoint for authentication
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

# Endpoint for login
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