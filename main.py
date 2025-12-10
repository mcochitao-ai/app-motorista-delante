import os
from functools import wraps
from pathlib import Path
import json
import urllib.parse

import psycopg2
import psycopg2.extras
from psycopg2 import pool

from flask import Flask, render_template, request, redirect, url_for, session, flash, g, abort
from werkzeug.security import generate_password_hash, check_password_hash
from google.auth.transport import requests
from google.oauth2 import id_token

BASE_DIR = Path(__file__).parent

# PostgreSQL connection pool
db_pool = None

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")
app.config["SESSION_COOKIE_SECURE"] = False  # True se usar HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 horas em segundos


def get_db():
    if "db" not in g:
        g.db = db_pool.getconn()
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db_pool.putconn(db)


def init_db():
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    email TEXT UNIQUE,
                    cnh TEXT,
                    phone TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
    finally:
        db_pool.putconn(conn)


def ensure_admin():
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "admin123")
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (admin_user,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "INSERT INTO users (name, username, password_hash, role) VALUES (%s, %s, %s, %s)",
                    ("Administrador", admin_user, generate_password_hash(admin_pass), "admin"),
                )
                conn.commit()
    finally:
        db_pool.putconn(conn)


def init_app():
    global db_pool
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,
        database_url,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    init_db()
    ensure_admin()


init_app()


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
    with db.cursor() as cur:
        cur.execute("SELECT id, name, username, role FROM users WHERE id = %s", (user_id,))
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
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, name, username, password_hash, role FROM users WHERE username = %s",
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
    return render_template("login.html", GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID", ""))


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
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, name, password_hash, cnh, phone, role) VALUES (%s, %s, %s, %s, %s, %s)",
                    (email, name, generate_password_hash(password), cnh, phone, "user"),
                )
            db.commit()
            flash("Conta criada! Faça login.", "success")
            return redirect(url_for("login"))
        except psycopg2.IntegrityError:
            db.rollback()
            flash("Email já cadastrado.", "error")
    return render_template("signup.html")


@app.route("/auth/google/callback", methods=["POST"])
def google_callback():
    """
    Google OAuth callback. Receives a token from the frontend after user authenticates.
    Verifies the token and creates/logs in the user.
    """
    try:
        token = request.json.get("credential")
        if not token:
            return {"error": "No token provided"}, 400

        # Verify the token
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                os.environ.get("GOOGLE_CLIENT_ID", "")
            )
        except Exception as e:
            return {"error": f"Token verification failed: {str(e)}"}, 401

        # Extract user info from token
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        picture = idinfo.get("picture", "")

        if not email:
            return {"error": "Email not found in token"}, 400

        db = get_db()

        # Check if user already exists
        with db.cursor() as cur:
            cur.execute("SELECT id, name, cnh, phone, role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if user:
            # User exists, log them in
            if not user["cnh"] or not user["phone"]:
                # User hasn't completed profile yet
                session["user_id"] = user["id"]
                session["email"] = email
                session.permanent = True
                return {"redirect": url_for("profile_create")}, 200
            else:
                # User profile is complete, log them in
                session["user_id"] = user["id"]
                session["username"] = email.split("@")[0]
                session["role"] = user["role"]
                session.permanent = True
                return {"redirect": url_for("home")}, 200
        else:
            # New user, create account with email
            # Generate a username from email
            username = email.split("@")[0]
            # Check if username exists
            counter = 1
            original_username = username
            while True:
                with db.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if not cur.fetchone():
                        break
                username = f"{original_username}{counter}"
                counter += 1

            # Create new user (but they need to complete profile first)
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, name, username, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                    (email, name, username, generate_password_hash("oauth"), "user"),
                )
            db.commit()

            # Get the new user
            with db.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                new_user = cur.fetchone()

            # Set session but redirect to profile creation
            session["user_id"] = new_user["id"]
            session["email"] = email
            session.permanent = True

            return {"redirect": url_for("profile_create")}, 200

    except Exception as e:
        return {"error": f"Internal error: {str(e)}"}, 500


@app.route("/profile/create", methods=["GET", "POST"])
@login_required
def profile_create():
    """
    Profile creation form for new OAuth users.
    Collects: nome completo, CNH, telefone, and sets password.
    """
    db = get_db()
    user_id = session.get("user_id")
    
    # Check if user already has a complete profile
    with db.cursor() as cur:
        cur.execute("SELECT cnh, phone FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
    
    if user and user["cnh"] and user["phone"]:
        # Profile already complete, redirect to home
        return redirect(url_for("home"))
    
    if request.method == "POST":
        cnh = request.form.get("cnh", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not all([cnh, phone, password, password_confirm]):
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("profile_create"))

        if password != password_confirm:
            flash("As senhas não conferem.", "error")
            return redirect(url_for("profile_create"))

        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "error")
            return redirect(url_for("profile_create"))

        # Update user profile
        with db.cursor() as cur:
            cur.execute(
                "UPDATE users SET cnh = %s, phone = %s, password_hash = %s WHERE id = %s",
                (cnh, phone, generate_password_hash(password), user_id),
            )
        db.commit()

        flash("Perfil criado com sucesso!", "success")
        return redirect(url_for("home"))

    return render_template("profile_create.html", user=g.user)


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
        email = request.form.get("email", "").strip()
        cnh = request.form.get("cnh", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        
        if not all([name, email, cnh, phone, password]):
            flash("Preencha todos os campos obrigatórios.", "error")
        elif len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "error")
        else:
            # Generate username from email
            username = email.split("@")[0]
            counter = 1
            original_username = username
            while True:
                with db.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if not cur.fetchone():
                        break
                username = f"{original_username}{counter}"
                counter += 1
            
            try:
                with db.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (name, email, username, password_hash, cnh, phone, role) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (name, email, username, generate_password_hash(password), cnh, phone, role),
                    )
                db.commit()
                flash("Usuário criado com sucesso.", "success")
            except psycopg2.IntegrityError:
                db.rollback()
                flash("Email já cadastrado.", "error")

    with db.cursor() as cur:
        cur.execute("SELECT id, name, email, username, cnh, phone, role FROM users ORDER BY id DESC")
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
