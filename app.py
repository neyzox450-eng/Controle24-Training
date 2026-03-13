from flask import Flask, request, redirect, session, render_template_string, url_for
import os
import requests

@app.route("/")
def home():
    return "Controle24 Training Website Online"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","devkey")

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID","")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET","")
DISCORD_REDIRECT_URI=https://controle24-training-production.up.railway.app/callback

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Controle24</title>
<style>
body{
font-family:Arial;
background:#0b0f1a;
color:white;
text-align:center;
padding:40px
}

button{
padding:12px 20px;
background:#5865F2;
border:none;
border-radius:8px;
color:white;
font-size:16px;
cursor:pointer
}

.card{
background:#151b2c;
padding:30px;
border-radius:12px;
display:inline-block
}
</style>
</head>

<body>

<div class="card">

<h1>Controle24</h1>

{% if not logged_in %}

<p>Connecte toi avec Discord</p>

<a href="/login">
<button>Login Discord</button>
</a>

{% else %}

<h2>Bienvenue {{username}}</h2>

<p>Tu es connecté.</p>

<a href="/logout">
<button>Logout</button>
</a>

{% endif %}

</div>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML,
        logged_in=bool(session.get("discord_id")),
        username=session.get("discord_name","")
    )

@app.route("/login")
def login():

    url = (
        "https://discord.com/api/oauth2/authorize"
        "?client_id="+DISCORD_CLIENT_ID+
        "&redirect_uri="+DISCORD_REDIRECT_URI+
        "&response_type=code"
        "&scope=identify"
    )

    return redirect(url)

@app.route("/callback")
def callback():

    code = request.args.get("code")

    if not code:
        return redirect("/")

    data = {
        "client_id":DISCORD_CLIENT_ID,
        "client_secret":DISCORD_CLIENT_SECRET,
        "grant_type":"authorization_code",
        "code":code,
        "redirect_uri":DISCORD_REDIRECT_URI
    }

    r = requests.post(
        "https://discord.com/api/oauth2/token",
        data=data,
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )

    token = r.json().get("access_token")

    user = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization":"Bearer "+token}
    ).json()

    session["discord_id"] = user["id"]
    session["discord_name"] = user["username"]

    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))