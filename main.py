import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash, g, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "app.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
        """
    )
    db.close()


def ensure_admin():
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "admin123")
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cur = db.execute("SELECT id FROM users WHERE username = ?", (admin_user,))
    row = cur.fetchone()
    if row is None:
        db.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Administrador", admin_user, generate_password_hash(admin_pass), "admin"),
        )
        db.commit()
    db.close()


init_db()
ensure_admin()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def load_user():
    user_id = session.get("user_id")
    if not user_id:
        g.user = None
        return
    db = get_db()
    cur = db.execute("SELECT id, name, username, role FROM users WHERE id = ?", (user_id,))
    g.user = cur.fetchone()


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("trip_form"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        cur = db.execute(
            "SELECT id, name, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        )
        user = cur.fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session.permanent = True
            flash("Login feito com sucesso.", "success")
            return redirect(url_for("trip_form"))
        flash("Usuário ou senha inválidos.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("login"))


@app.route("/form", methods=["GET", "POST"])
@login_required
def trip_form():
    message = None
    if request.method == "POST":
        message = "Viagem registrada. Ajuste o backend para salvar no banco ou enviar ao seu sistema."
        flash(message, "success")
        return redirect(url_for("trip_form"))
    return render_template("trip_form.html", user=g.user)


@app.route("/dashboard", methods=["GET", "POST"])
@admin_required
def dashboard():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        if not all([name, username, password]):
            flash("Preencha nome, usuário e senha.", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
                    (name, username, generate_password_hash(password), role),
                )
                db.commit()
                flash("Usuário criado.", "success")
            except sqlite3.IntegrityError:
                flash("Usuário já existe.", "error")

    cur = db.execute("SELECT id, name, username, role FROM users ORDER BY id DESC")
    users = cur.fetchall()
    return render_template("dashboard.html", users=users)


@app.errorhandler(403)
def forbidden(_):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    # Disable reloader in Windows to avoid watchdog thread handle issues.
    app.run(
        debug=debug,
        use_reloader=debug,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
