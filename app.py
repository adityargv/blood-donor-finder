from flask import Flask
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
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
    return "Blood Donor Finder is running!"

if __name__ == "__main__":
    init_db()
    app.run(debug=True) 