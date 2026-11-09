from flask import Flask, request, jsonify, render_template
import sqlite3
import json
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

    # Nieuwe tabel om per gebruiker bij te houden welke puzzels zijn opgelost
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

# --- Pagina Routes ---
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


# --- API Endpoints voor Deelnemers/Scores ---
@app.route("/api/deelnemers", methods=["GET"])
def get_deelnemers():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # We halen de naam en score op uit deelnemers
    cursor.execute("SELECT naam, score FROM deelnemers")
    rows = cursor.fetchall()
    
    resultaat = []
    for row in rows:
        naam = row[0]
        score = row[1]
        
        # Tel hoeveel unieke puzzels deze gebruiker daadwerkelijk heeft opgelost (voor de tiebreaker/weergave)
        cursor.execute("SELECT COUNT(*) FROM gebruiker_puzzels WHERE naam = ?", (naam,))
        aantal_opgelost = cursor.fetchone()[0]
        
        resultaat.append({
            "naam": naam,
            "score": score,             # Totale punten
            "opgelost": aantal_opgelost # Aantal opgeloste puzzels
        })
        
    conn.close()
    
    # Sorteer direct vanuit Flask of laat JS het doen; we sorteren hier op score (hoogste eerst)
    resultaat.sort(key=lambda x: (x["score"], x["opgelost"]), reverse=True)
    
    return jsonify(resultaat)

@app.route("/api/deelnemers", methods=["POST"])
def add_or_update_deelnemer():
    data = request.json
    naam = data.get("naam")
    puzzels = data.get("puzzels", []) # Lijst van opgeloste puzzelnummers

    if not naam:
        return jsonify({"error": "Ongeldige invoer"}), 400

    # Laad de puzzels uit het JSON-bestand om de punten op te tellen
    try:
        with open("puzzels.json", "r", encoding="utf-8") as f:
            puzzels_lijst = json.load(f)
    except FileNotFoundError:
        puzzels_lijst = []

    # Maak een dictionary van puzzel_nummer -> punten
    punten_map = {p["nummer"]: p.get("punten", 1) for p in puzzels_lijst}

    # Bereken de totale score op basis van de punten van de aangevinkte puzzels
    score = sum(punten_map.get(p_nr, 1) for p_nr in puzzels)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # 1. Update totale score in deelnemers tabel
    cursor.execute("""
        INSERT INTO deelnemers (naam, score) VALUES (?, ?)
        ON CONFLICT(naam) DO UPDATE SET score=excluded.score
    """, (naam, score))
    
    # 2. Verwijder oude vinkjes en sla de nieuwe op
    cursor.execute("DELETE FROM gebruiker_puzzels WHERE naam = ?", (naam,))
    for p_nr in puzzels:
        cursor.execute("INSERT OR IGNORE INTO gebruiker_puzzels (naam, puzzel_nr) VALUES (?, ?)", (naam, p_nr))
        
    conn.commit()
    conn.close()
    return jsonify({"message": "Succesvol opgeslagen"}), 200

# --- API Endpoint om opgeslagen puzzels van een gebruiker op te halen ---
@app.route("/api/gebruiker-puzzels/<naam>", methods=["GET"])
def get_gebruiker_puzzels(naam):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT puzzel_nr FROM gebruiker_puzzels WHERE naam = ?", (naam,))
    rows = cursor.fetchall()
    conn.close()
    
    puzzels = [row[0] for row in rows]
    return jsonify(puzzels)

# --- API Endpoints for which participants did which questions ---
@app.route("/api/questions", methods=["GET"])
def get_questions():
    try:
        with open("puzzels.json", "r", encoding="utf-8") as f:
            puzzels_lijst = json.load(f)
    except FileNotFoundError:
        puzzels_lijst = []

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Tel het totale aantal unieke gebruikers voor het percentage
    cursor.execute("SELECT COUNT(DISTINCT gebruikersnaam) FROM gebruikers")
    totaal_row = cursor.fetchone()
    totaal_gebruikers = totaal_row[0] if totaal_row and totaal_row[0] > 0 else 1
    
    resultaat = []
    
    for p in puzzels_lijst:
        p_nr = p["nummer"]
        p_naam = p.get("naam", f"Puzzel {p_nr}")
        p_punten = p.get("punten", 1)  # Haal de punten op uit JSON
        
        # Haal de namen op die deze puzzel hebben opgelost
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
    
    # Sorteer primair op aantal oplossers (aflopend: -x["aantal"] zet de meeste oplossers bovenaan)
    # Secundair (tiebreaker): op punten (oplopend: x["punten"])
    resultaat.sort(key=lambda x: (-x["aantal"], x["punten"]))
    
    return jsonify(resultaat)

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