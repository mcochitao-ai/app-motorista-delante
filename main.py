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
app.config["SESSION_COOKIE_SECURE"] = False  # True se usar HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 horas em segundos


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
            username TEXT UNIQUE,
            password_hash TEXT,
            email TEXT UNIQUE,
            cnh TEXT,
            phone TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    # Limpa g.user primeiro
    g.user = None
    
    user_id = session.get("user_id")
    if not user_id:
        return
    
    db = get_db()
    cur = db.execute("SELECT id, name, username, role FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    
    # Valida se o user_id da sessão ainda existe no banco
    if user:
        g.user = user
    else:
        # Se o usuário não existe mais, limpa a sessão
        session.clear()


@app.route("/")
def index():
    # Verifica se tem sessão válida E se o usuário existe
    if session.get("user_id") and g.user:
        return redirect(url_for("home"))
    # Se não tem sessão válida, limpa tudo e vai pro login
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
@login_required
def home():
    # Mock data - substituir por consulta real ao banco quando implementar salvamento
    stats = {
        "total": 0,
        "finalizadas": 0,
        "devolucoes": 0,
        "hoje": 0
    }
    recent_trips = []
    # Exemplo de estrutura esperada quando tiver dados reais:
    # recent_trips = [
    #     {"date": "05/12/2025", "status": "finalizado", "driver": "João Silva", "helper": "Pedro"},
    #     {"date": "04/12/2025", "status": "devolucao", "driver": "João Silva", "helper": None}
    # ]
    return render_template("home.html", stats=stats, recent_trips=recent_trips)


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
            return redirect(url_for("home"))
        flash("Usuário ou senha inválidos.", "error")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        cnh = request.form.get("cnh", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([email, name, password, cnh, phone]):
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("signup"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (email, name, password_hash, cnh, phone, role) VALUES (?, ?, ?, ?, ?, ?)",
                (email, name, generate_password_hash(password), cnh, phone, "user"),
            )
            db.commit()
            flash("Conta criada! Faça login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email já cadastrado.", "error")
    return render_template("signup.html")


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
