from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date, datetime
from functools import wraps
from math import radians, sin, cos, asin, sqrt
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-to-any-random-text"
ADMIN_PASSWORD = "admin123"


# ---------- Database helpers ----------

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
            last_donated_date TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    # Older databases do not have the location columns yet, so add them.
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(donors)")]
    if "latitude" not in columns:
        conn.execute("ALTER TABLE donors ADD COLUMN latitude REAL")
    if "longitude" not in columns:
        conn.execute("ALTER TABLE donors ADD COLUMN longitude REAL")
    conn.commit()
    conn.close()


# ---------- Other helpers ----------

def is_eligible(last_donated):
    if not last_donated:
        return True
    last = datetime.strptime(last_donated, "%Y-%m-%d").date()
    return (date.today() - last).days >= 90


def parse_location(form):
    """Returns (latitude, longitude, error). Both empty is allowed."""
    lat_raw = form.get("latitude", "").strip()
    lng_raw = form.get("longitude", "").strip()
    if not lat_raw and not lng_raw:
        return None, None, None
    try:
        lat = float(lat_raw)
        lng = float(lng_raw)
    except ValueError:
        return None, None, "Latitude and longitude must be numbers (or both left empty)."
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, None, "Location is out of range."
    # Rounded to 3 decimals (about 100 m) to protect the donor's privacy.
    return round(lat, 3), round(lng, 3), None


def distance_km(lat1, lng1, lat2, lng2):
    """Haversine formula: distance in km between two latitude/longitude points."""
    earth_radius = 6371
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return 2 * earth_radius * asin(sqrt(a))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ---------- Public pages ----------

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
        latitude, longitude, location_error = parse_location(request.form)

        error = None
        if not phone.isdigit() or len(phone) != 10:
            error = "Phone number must be exactly 10 digits."
        elif location_error:
            error = location_error
        if error:
            return render_template("register.html", error=error, f=request.form)

        conn = get_db()
        conn.execute(
            "INSERT INTO donors (name, blood_group, city, phone, last_donated_date, "
            "latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, blood_group, city, phone, last_donated, latitude, longitude)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("donors"))

    return render_template("register.html", f={})


@app.route("/donors")
def donors():
    conn = get_db()
    rows = conn.execute("SELECT * FROM donors").fetchall()
    conn.close()
    donors_list = [dict(r, eligible=is_eligible(r["last_donated_date"])) for r in rows]
    return render_template("donors.html", donors=donors_list)


@app.route("/search")
def search():
    blood_group = request.args.get("blood_group", "")
    city = request.args.get("city", "").strip()
    only_eligible = request.args.get("only_eligible") == "on"
    radius = request.args.get("radius", "")
    searched = "blood_group" in request.args

    # The visitor's GPS position (sent by the "Find donors near me" button)
    near = None
    try:
        user_lat = float(request.args.get("lat", ""))
        user_lng = float(request.args.get("lng", ""))
        if -90 <= user_lat <= 90 and -180 <= user_lng <= 180:
            near = (user_lat, user_lng)
    except ValueError:
        pass

    donors = []
    skipped = 0  # donors without a saved location, left out of a "near me" search
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
        rows = conn.execute(query, params).fetchall()
        conn.close()
        donors = [dict(r, eligible=is_eligible(r["last_donated_date"])) for r in rows]
        if only_eligible:
            donors = [d for d in donors if d["eligible"]]

        if near:
            with_distance = []
            for d in donors:
                if d["latitude"] is None or d["longitude"] is None:
                    skipped += 1
                    continue
                d["distance"] = round(distance_km(near[0], near[1],
                                                  d["latitude"], d["longitude"]), 1)
                with_distance.append(d)
            if radius:
                try:
                    with_distance = [d for d in with_distance if d["distance"] <= float(radius)]
                except ValueError:
                    pass
            donors = sorted(with_distance, key=lambda d: d["distance"])

    return render_template("search.html", donors=donors, city=city,
                           blood_group=blood_group, only_eligible=only_eligible,
                           radius=radius, searched=searched,
                           near=near is not None, skipped=skipped)


@app.route("/map")
def map_view():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM donors WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    ).fetchall()
    conn.close()
    donors_list = [dict(r, eligible=is_eligible(r["last_donated_date"])) for r in rows]
    return render_template("map.html", donors=donors_list)


# ---------- Admin login ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        return render_template("login.html", error="Wrong password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


# ---------- Admin panel (protected) ----------

@app.route("/admin")
@login_required
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM donors ORDER BY id").fetchall()
    conn.close()
    return render_template("admin.html", donors=rows)


@app.route("/edit/<int:donor_id>", methods=["GET", "POST"])
@login_required
def edit(donor_id):
    conn = get_db()
    donor = conn.execute("SELECT * FROM donors WHERE id = ?", (donor_id,)).fetchone()
    if donor is None:
        conn.close()
        return redirect(url_for("admin"))

    if request.method == "POST":
        name = request.form["name"].strip()
        blood_group = request.form["blood_group"]
        city = request.form["city"].strip()
        phone = request.form["phone"].strip()
        last_donated = request.form["last_donated_date"] or None
        latitude, longitude, location_error = parse_location(request.form)

        error = None
        if not phone.isdigit() or len(phone) != 10:
            error = "Phone number must be exactly 10 digits."
        elif location_error:
            error = location_error
        if error:
            conn.close()
            return render_template("edit.html", donor=donor, error=error)

        conn.execute(
            "UPDATE donors SET name=?, blood_group=?, city=?, phone=?, "
            "last_donated_date=?, latitude=?, longitude=? WHERE id=?",
            (name, blood_group, city, phone, last_donated, latitude, longitude, donor_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    conn.close()
    return render_template("edit.html", donor=donor)


@app.route("/delete/<int:donor_id>", methods=["POST"])
@login_required
def delete(donor_id):
    conn = get_db()
    conn.execute("DELETE FROM donors WHERE id = ?", (donor_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)