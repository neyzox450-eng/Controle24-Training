import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from functools import wraps
from urllib.parse import urlencode

import requests
from flask import Flask, request, redirect, session, url_for, render_template_string, flash, g


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DATABASE = "database.db"
ADMIN_ID = "1245739031397142621"

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "")

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"


BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title or "Control 24 Training" }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root{
            --bg:#0b1a2e;
            --bg2:#10233c;
            --panel:#122844;
            --panel2:#163150;
            --amber:#f5a623;
            --teal:#00c8aa;
            --text:#e8f1ff;
            --muted:#9cb3cf;
            --danger:#ff6b6b;
            --success:#39d98a;
            --border:rgba(255,255,255,0.08);
            --shadow:0 12px 30px rgba(0,0,0,0.35);
        }
        *{box-sizing:border-box}
        body{
            margin:0;
            font-family:'Rajdhani',sans-serif;
            background:
                radial-gradient(circle at top right, rgba(0,200,170,0.08), transparent 25%),
                radial-gradient(circle at top left, rgba(245,166,35,0.08), transparent 25%),
                linear-gradient(180deg, var(--bg), #081220 100%);
            color:var(--text);
            min-height:100vh;
        }
        .nav{
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:18px 28px;
            border-bottom:1px solid var(--border);
            background:rgba(8,18,32,0.7);
            backdrop-filter: blur(8px);
            position:sticky;
            top:0;
            z-index:10;
        }
        .brand{
            font-family:'Share Tech Mono', monospace;
            font-size:1.1rem;
            letter-spacing:1px;
            color:var(--amber);
            text-decoration:none;
        }
        .nav-links{
            display:flex;
            gap:12px;
            align-items:center;
            flex-wrap:wrap;
        }
        .nav-links a, .btn{
            text-decoration:none;
            color:var(--text);
            padding:10px 16px;
            border:1px solid var(--border);
            background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
            clip-path:polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
            transition:0.2s ease;
            cursor:pointer;
            font-family:'Rajdhani',sans-serif;
            font-weight:600;
        }
        .nav-links a:hover, .btn:hover{
            border-color:rgba(245,166,35,0.5);
            transform:translateY(-1px);
        }
        .btn-primary{
            background:linear-gradient(135deg, rgba(245,166,35,0.2), rgba(245,166,35,0.05));
            border-color:rgba(245,166,35,0.5);
        }
        .btn-secondary{
            background:linear-gradient(135deg, rgba(0,200,170,0.2), rgba(0,200,170,0.05));
            border-color:rgba(0,200,170,0.5);
        }
        .btn-danger{
            background:linear-gradient(135deg, rgba(255,107,107,0.18), rgba(255,107,107,0.05));
            border-color:rgba(255,107,107,0.45);
        }
        .container{
            max-width:1180px;
            margin:32px auto;
            padding:0 20px 40px;
        }
        .hero{
            display:grid;
            grid-template-columns:1.1fr 0.9fr;
            gap:24px;
            align-items:stretch;
        }
        .card{
            background:linear-gradient(180deg, rgba(18,40,68,0.95), rgba(10,24,42,0.98));
            border:1px solid var(--border);
            box-shadow:var(--shadow);
            padding:24px;
            clip-path:polygon(18px 0, 100% 0, 100% calc(100% - 18px), calc(100% - 18px) 100%, 0 100%, 0 18px);
        }
        h1,h2,h3{margin-top:0}
        h1{
            font-size:3rem;
            line-height:0.95;
            margin-bottom:14px;
        }
        .accent-amber{color:var(--amber)}
        .accent-teal{color:var(--teal)}
        .lead{
            color:var(--muted);
            font-size:1.15rem;
            line-height:1.5;
        }
        .grid{
            display:grid;
            gap:22px;
        }
        .grid-2{
            grid-template-columns:1fr 1fr;
        }
        label{
            display:block;
            font-weight:600;
            margin-bottom:8px;
            letter-spacing:0.2px;
        }
        input, select, textarea{
            width:100%;
            padding:14px 14px;
            border:1px solid rgba(255,255,255,0.10);
            background:rgba(255,255,255,0.03);
            color:var(--text);
            outline:none;
            font-family:'Rajdhani',sans-serif;
            font-size:1rem;
            clip-path:polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
        }
        select option {
            color:#000;
        }
        textarea{min-height:130px; resize:vertical}
        input:focus, select:focus, textarea:focus{
            border-color:rgba(0,200,170,0.5);
            box-shadow:0 0 0 3px rgba(0,200,170,0.12);
        }
        .flash{
            padding:14px 16px;
            margin-bottom:16px;
            border:1px solid var(--border);
            background:rgba(255,255,255,0.03);
            clip-path:polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
        }
        .flash.success{border-color:rgba(57,217,138,0.4); color:#bcffd8}
        .flash.error{border-color:rgba(255,107,107,0.4); color:#ffd3d3}
        .flash.info{border-color:rgba(245,166,35,0.4); color:#ffe3b0}
        .meta{
            display:flex;
            gap:18px;
            flex-wrap:wrap;
            color:var(--muted);
            font-family:'Share Tech Mono', monospace;
            font-size:0.88rem;
        }
        table{
            width:100%;
            border-collapse:collapse;
            overflow:hidden;
        }
        th, td{
            text-align:left;
            padding:14px 12px;
            border-bottom:1px solid rgba(255,255,255,0.06);
            vertical-align:top;
        }
        th{
            color:var(--amber);
            font-family:'Share Tech Mono', monospace;
            font-size:0.88rem;
            letter-spacing:0.4px;
        }
        .actions{
            display:flex;
            gap:10px;
            flex-wrap:wrap;
        }
        .small{
            font-size:0.92rem;
            color:var(--muted);
        }
        .badge{
            display:inline-block;
            padding:5px 10px;
            border:1px solid var(--border);
            font-size:0.85rem;
            font-family:'Share Tech Mono', monospace;
            color:var(--teal);
            background:rgba(0,200,170,0.08);
            clip-path:polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
        }
        .section-title{
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:12px;
            margin-bottom:16px;
        }
        .empty{
            color:var(--muted);
            padding:18px;
            border:1px dashed rgba(255,255,255,0.12);
        }
        .footer-note{
            margin-top:28px;
            color:var(--muted);
            font-size:0.95rem;
            text-align:center;
        }
        @media (max-width: 920px){
            .hero, .grid-2{
                grid-template-columns:1fr;
            }
            h1{font-size:2.25rem}
            .nav{padding:16px 16px}
            .container{padding:0 14px 36px}
        }
    </style>
</head>
<body>
    <nav class="nav">
        <a class="brand" href="{{ url_for('index') }}">CONTROL24 // TRAINING OPS</a>
        <div class="nav-links">
            <a href="{{ url_for('index') }}">Home</a>
            {% if session.get('user') %}
                <a href="{{ url_for('request_training') }}">Training Request</a>
                {% if is_staff_session() %}
                    <a href="{{ url_for('dashboard') }}">Dashboard</a>
                {% endif %}
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a class="btn-primary" href="{{ url_for('login') }}">Login with Discord</a>
            {% endif %}
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ content|safe }}
    </div>
</body>
</html>
"""


INDEX_CONTENT = """
<div class="hero">
    <div class="card">
        <div class="badge">IVAO-STYLE TRAINING PORTAL</div>
        <h1><span class="accent-amber">Training</span><br><span class="accent-teal">Request Center</span></h1>
        <p class="lead">
            Submit your ATC training request through the official Control 24 training portal.
            Requests are reviewed by the training staff and instructors.
        </p>
        <div class="meta" style="margin:18px 0 22px;">
            <span>OAuth2 / Discord</span>
            <span>Gmail SMTP Notifications</span>
            <span>Staff Dashboard</span>
        </div>
        {% if session.get('user') %}
            <div class="actions">
                <a class="btn btn-primary" href="{{ url_for('request_training') }}">Submit a Request</a>
                {% if is_staff_session() %}
                    <a class="btn btn-secondary" href="{{ url_for('dashboard') }}">Open Dashboard</a>
                {% endif %}
            </div>
        {% else %}
            <div class="actions">
                <a class="btn btn-primary" href="{{ url_for('login') }}">Login with Discord</a>
            </div>
        {% endif %}
    </div>

    <div class="card">
        <h2>Operational Rules</h2>
        <p class="small">
            Once a request is accepted, the trainee will receive an email confirmation.
            An instructor will then contact the trainee via Discord private message.
        </p>
        <p class="small">
            <strong>Important:</strong> it is strictly forbidden for the trainee to contact the instructor first.
        </p>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:20px 0;">
        <h3>Required Information</h3>
        <ul style="color:var(--muted); line-height:1.8; padding-left:20px;">
            <li>Full identity details</li>
            <li>Current ATC rank</li>
            <li>Target rank</li>
            <li>Availability for training</li>
            <li>Valid email address</li>
        </ul>
    </div>
</div>

<div class="footer-note">
    Control 24 Training Department — secure intake portal for training requests.
</div>
"""


REQUEST_CONTENT = """
<div class="card" style="max-width:900px;margin:0 auto;">
    <div class="section-title">
        <div>
            <div class="badge">TRAINING INTAKE FORM</div>
            <h2 style="margin:10px 0 0;">Submit a Training Request</h2>
        </div>
        <div class="small">
            Logged in as {{ session['user']['username'] }}<br>
            Discord ID: {{ session['user']['id'] }}
        </div>
    </div>

    <form method="post" class="grid">
        <div class="grid grid-2">
            <div>
                <label>Nom</label>
                <input type="text" name="nom" required>
            </div>
            <div>
                <label>Prénom</label>
                <input type="text" name="prenom" required>
            </div>
        </div>

        <div class="grid grid-2">
            <div>
                <label>Email</label>
                <input type="email" name="email" value="{{ session['user'].get('email', '') }}" required>
            </div>
            <div>
                <label>Rang actuel</label>
                <select name="rang_actuel" required>
                    <option value="">Select current rank</option>
                    <option value="DEL">DEL</option>
                    <option value="GND">GND</option>
                    <option value="TWR">TWR</option>
                    <option value="APP">APP</option>
                    <option value="CTR">CTR</option>
                    <option value="U_CTR">U_CTR</option>
                </select>
            </div>
        </div>

        <div class="grid grid-2">
            <div>
                <label>Rang visé</label>
                <input type="text" name="rang_vise" required>
            </div>
            <div>
                <label>Disponibilités</label>
                <input type="text" name="disponibilites" placeholder="Example: Weekdays after 18:00 / Saturday afternoon" required>
            </div>
        </div>

        <div style="display:flex;justify-content:flex-end;">
            <button class="btn btn-primary" type="submit">Submit Request</button>
        </div>
    </form>
</div>
"""


DASHBOARD_CONTENT = """
<div class="grid">
    <div class="card">
        <div class="section-title">
            <div>
                <div class="badge">STAFF OPERATIONS</div>
                <h2 style="margin:10px 0 0;">Pending Training Requests</h2>
            </div>
            <div class="small">
                Connected as {{ session['user']['username'] }}<br>
                Role:
                {% if session['user']['id'] == admin_id %}
                    Admin
                {% else %}
                    Instructor
                {% endif %}
            </div>
        </div>

        {% if requests_list %}
        <div style="overflow-x:auto;">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Applicant</th>
                        <th>Email</th>
                        <th>Current Rank</th>
                        <th>Target Rank</th>
                        <th>Availability</th>
                        <th>Discord ID</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for req in requests_list %}
                    <tr>
                        <td>#{{ req['id'] }}</td>
                        <td>{{ req['nom'] }} {{ req['prenom'] }}</td>
                        <td>{{ req['email'] }}</td>
                        <td>{{ req['rang_actuel'] }}</td>
                        <td>{{ req['rang_vise'] }}</td>
                        <td>{{ req['disponibilites'] }}</td>
                        <td>{{ req['discord_id'] }}</td>
                        <td>
                            <div class="actions">
                                <form method="post" action="{{ url_for('accept_request', request_id=req['id']) }}">
                                    <button class="btn btn-secondary" type="submit">Accept</button>
                                </form>
                                <form method="post" action="{{ url_for('reject_request', request_id=req['id']) }}">
                                    <button class="btn btn-danger" type="submit">Reject</button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
            <div class="empty">No pending requests at the moment.</div>
        {% endif %}
    </div>

    {% if session['user']['id'] == admin_id %}
    <div class="grid grid-2">
        <div class="card">
            <div class="badge">ADMIN ONLY</div>
            <h2 style="margin-top:10px;">Add Instructor</h2>
            <form method="post" action="{{ url_for('add_instructor') }}" class="grid">
                <div>
                    <label>Discord User ID</label>
                    <input type="text" name="discord_id" required>
                </div>
                <div>
                    <label>Name</label>
                    <input type="text" name="nom" required>
                </div>
                <div style="display:flex;justify-content:flex-end;">
                    <button class="btn btn-primary" type="submit">Add Instructor</button>
                </div>
            </form>
        </div>

        <div class="card">
            <div class="badge">INSTRUCTOR ROSTER</div>
            <h2 style="margin-top:10px;">Manage Instructors</h2>
            {% if instructors %}
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Discord ID</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for instructor in instructors %}
                            <tr>
                                <td>{{ instructor['nom'] }}</td>
                                <td>{{ instructor['discord_id'] }}</td>
                                <td>
                                    <form method="post" action="{{ url_for('remove_instructor', instructor_id=instructor['id']) }}">
                                        <button class="btn btn-danger" type="submit">Remove</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <div class="empty">No instructors added yet.</div>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT NOT NULL,
            rang_actuel TEXT NOT NULL,
            rang_vise TEXT NOT NULL,
            disponibilites TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL
        )
        """
    )
    db.commit()


def render_page(content_template, **context):
    content = render_template_string(content_template, **context)
    return render_template_string(
        BASE_HTML,
        content=content,
        is_staff_session=is_staff_session,
        **context
    )


def send_email(to_email, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_PASSWORD:
        print("Gmail credentials are missing. Email not sent.")
        return False

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [to_email], msg.as_string())

        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def is_instructor(discord_id):
    db = get_db()
    row = db.execute(
        "SELECT id FROM instructors WHERE discord_id = ?",
        (discord_id,)
    ).fetchone()
    return row is not None


def is_staff_session():
    user = session.get("user")
    if not user:
        return False

    discord_id = user.get("id")
    return discord_id == ADMIN_ID or is_instructor(discord_id)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            flash("You must log in with Discord first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            flash("You must log in first.", "error")
            return redirect(url_for("login"))
        if not is_staff_session():
            flash("Access denied.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if not user or user.get("id") != ADMIN_ID:
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


@app.before_request
def before_request():
    init_db()


@app.route("/")
def index():
    return render_page(INDEX_CONTENT, title="Control 24 Training Portal")


@app.route("/login")
def login():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET or not DISCORD_REDIRECT_URI:
        flash("Discord OAuth variables are missing on Railway.", "error")
        return redirect(url_for("index"))

    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify email",
        "prompt": "consent",
    }
    return redirect(f"{DISCORD_AUTH_URL}?{urlencode(params)}")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        flash("Discord authorization failed.", "error")
        return redirect(url_for("index"))

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": "identify email",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token_response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers, timeout=20)
    if token_response.status_code != 200:
        flash("Failed to retrieve Discord access token.", "error")
        return redirect(url_for("index"))

    access_token = token_response.json().get("access_token")
    if not access_token:
        flash("Discord access token missing.", "error")
        return redirect(url_for("index"))

    user_response = requests.get(
        DISCORD_USER_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20
    )

    if user_response.status_code != 200:
        flash("Failed to retrieve Discord user information.", "error")
        return redirect(url_for("index"))

    user_data = user_response.json()

    session["user"] = {
        "id": str(user_data.get("id", "")),
        "username": user_data.get("username", "UnknownUser"),
        "email": user_data.get("email", ""),
    }

    flash("Successfully logged in with Discord.", "success")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/request", methods=["GET", "POST"])
@login_required
def request_training():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()
        email = request.form.get("email", "").strip()
        rang_actuel = request.form.get("rang_actuel", "").strip()
        rang_vise = request.form.get("rang_vise", "").strip()
        disponibilites = request.form.get("disponibilites", "").strip()

        if not all([nom, prenom, email, rang_actuel, rang_vise, disponibilites]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for("request_training"))

        db = get_db()
        db.execute(
            """
            INSERT INTO requests (
                discord_id, nom, prenom, email, rang_actuel, rang_vise, disponibilites, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                session["user"]["id"],
                nom,
                prenom,
                email,
                rang_actuel,
                rang_vise,
                disponibilites,
            ),
        )
        db.commit()

        send_email(
            email,
            "Training Request Received",
            """Hello,

Your training request has been successfully received by the Control 24 Training Department.

Your request will be reviewed by an instructor.

You will receive another email once your request has been accepted or refused.

Best regards,
Control 24 Training Department""",
        )

        flash("Your training request has been submitted successfully.", "success")
        return redirect(url_for("index"))

    return render_page(REQUEST_CONTENT, title="Submit Training Request")


@app.route("/dashboard")
@staff_required
def dashboard():
    db = get_db()

    requests_list = db.execute(
        "SELECT * FROM requests WHERE status = 'pending' ORDER BY id DESC"
    ).fetchall()

    instructors = db.execute(
        "SELECT * FROM instructors ORDER BY id DESC"
    ).fetchall()

    return render_page(
        DASHBOARD_CONTENT,
        title="Staff Dashboard",
        requests_list=requests_list,
        instructors=instructors,
        admin_id=ADMIN_ID,
    )


@app.route("/accept/<int:request_id>", methods=["POST"])
@staff_required
def accept_request(request_id):
    db = get_db()

    req = db.execute(
        "SELECT * FROM requests WHERE id = ?",
        (request_id,)
    ).fetchone()

    if not req:
        flash("Request not found.", "error")
        return redirect(url_for("dashboard"))

    db.execute(
        "UPDATE requests SET status = 'accepted' WHERE id = ?",
        (request_id,)
    )
    db.commit()

    send_email(
        req["email"],
        "Training Request Accepted",
        """Hello,

Your training request has been accepted by the Control 24 Training Department.

An instructor will contact you soon via Discord private message.

Important:
You are NOT allowed to contact your instructor first.

Please wait until they contact you.

Best regards,
Control 24 Training Department""",
    )

    flash(f"Request #{request_id} accepted and confirmation email sent.", "success")
    return redirect(url_for("dashboard"))


@app.route("/reject/<int:request_id>", methods=["POST"])
@staff_required
def reject_request(request_id):
    db = get_db()

    req = db.execute(
        "SELECT * FROM requests WHERE id = ?",
        (request_id,)
    ).fetchone()

    if not req:
        flash("Request not found.", "error")
        return redirect(url_for("dashboard"))

    db.execute(
        "UPDATE requests SET status = 'refused' WHERE id = ?",
        (request_id,)
    )
    db.commit()

    send_email(
        req["email"],
        "Training Request Refused",
        """Hello,

Unfortunately your training request has been refused.

You may submit another request in the future.

Best regards,
Control 24 Training Department""",
    )

    flash(f"Request #{request_id} refused and email sent.", "info")
    return redirect(url_for("dashboard"))


@app.route("/admin/instructors/add", methods=["POST"])
@staff_required
@admin_required
def add_instructor():
    discord_id = request.form.get("discord_id", "").strip()
    nom = request.form.get("nom", "").strip()

    if not discord_id or not nom:
        flash("Both Discord ID and name are required.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO instructors (discord_id, nom) VALUES (?, ?)",
            (discord_id, nom),
        )
        db.commit()
        flash("Instructor added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("This instructor already exists.", "error")

    return redirect(url_for("dashboard"))


@app.route("/admin/instructors/remove/<int:instructor_id>", methods=["POST"])
@staff_required
@admin_required
def remove_instructor(instructor_id):
    db = get_db()
    db.execute("DELETE FROM instructors WHERE id = ?", (instructor_id,))
    db.commit()
    flash("Instructor removed successfully.", "info")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)