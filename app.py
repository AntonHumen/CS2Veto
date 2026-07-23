import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "my_secret_key"


def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS maps(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT UNIQUE,
        name_ua TEXT,
        image_name TEXT
    )
    """
    )

    cursor.execute("SELECT COUNT(*) FROM maps")
    if cursor.fetchone()[0] == 0:
        cs2_maps = [
            ("Mirage", "Міраж", "mirage.jpg"),
            ("Inferno", "Інферно", "inferno.jpg"),
            ("Nuke", "Нюк", "nuke.jpg"),
            ("Ancient", "Ейншент", "ancient.jpg"),
            ("Anubis", "Анубіс", "anubis.jpg"),
            ("Dust 2", "Даст 2", "dust2.jpg"),
            ("Cache", "Кеш", "cache.jpg"),
        ]
        cursor.executemany(
            "INSERT INTO maps(name_en, name_ua, image_name) VALUES(?,?,?)",
            cs2_maps,
        )

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    if "user" in session:
        if "match_format" not in session:
            return redirect("/format")
        if "team_a" not in session or "team_b" not in session:
            return redirect("/setup")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maps")
        maps_data = cursor.fetchall()
        conn.close()

        return render_template(
            "index.html",
            user=session["user"],
            maps=maps_data,
            team_a=session["team_a"],
            team_b=session["team_b"],
            match_format=session["match_format"],
        )
    return redirect("/login")


@app.route("/format", methods=["GET", "POST"])
def select_format():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        selected = request.form.get("match_format", "bo3")
        session["match_format"] = selected
        return redirect("/setup")

    return render_template("format.html")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        team_a = request.form.get("team_a", "").strip()
        team_b = request.form.get("team_b", "").strip()

        if not team_a or not team_b:
            flash("Введіть назви обох команд!", "error")
            return redirect("/setup")

        session["team_a"] = team_a
        session["team_b"] = team_b
        return redirect("/")

    return render_template("setup.html", match_format=session.get("match_format", "bo3"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password),
            )
            conn.commit()
            conn.close()
            flash("Реєстрація успішна! Тепер увійдіть.", "success")
            return redirect("/login")
        except:
            flash("Користувач з таким логіном уже існує!", "error")
            return redirect("/register")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/format")

        flash("Невірний логін або пароль!", "error")
        return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)