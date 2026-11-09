from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            last_donated_date TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        blood_group = request.form["blood_group"]
        city = request.form["city"].strip()
        phone = request.form["phone"].strip()
        last_donated = request.form["last_donated_date"] or None

        if not phone.isdigit() or len(phone) != 10:
            return render_template("register.html",
                                   error="Phone number must be exactly 10 digits.")

        conn = get_db()
        conn.execute(
            "INSERT INTO donors (name, blood_group, city, phone, last_donated_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, blood_group, city, phone, last_donated)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("donors"))

    return render_template("register.html")

@app.route("/donors")
def donors():
    conn = get_db()
    rows = conn.execute("SELECT * FROM donors").fetchall()
    conn.close()
    return render_template("donors.html", donors=rows)
@app.route("/search")
def search():
    blood_group = request.args.get("blood_group", "")
    city = request.args.get("city", "").strip()
    searched = "blood_group" in request.args

    donors = []
    if searched:
        query = "SELECT * FROM donors WHERE 1=1"
        params = []
        if blood_group:
            query += " AND blood_group = ?"
            params.append(blood_group)
        if city:
            query += " AND LOWER(city) = LOWER(?)"
            params.append(city)
        conn = get_db()
        donors = conn.execute(query, params).fetchall()
        conn.close()

    return render_template("search.html", donors=donors,
                           city=city, searched=searched)
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    