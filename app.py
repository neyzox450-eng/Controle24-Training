import os
import requests
import smtplib
from email.mime.text import MIMEText
from flask import Flask, redirect, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "YOUR_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "https://controle24-training-production.up.railway.app/callback")

GMAIL_EMAIL = os.environ.get("GMAIL_EMAIL", "yourgmail@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "gmailapppassword")

DISCORD_API = "https://discord.com/api"


@app.route("/")
def home():
    return """
    <h1>Controle24 Training</h1>
    <p>Welcome to the Controle24 training platform.</p>
    <a href='/login'>Login with Discord</a>
    """


@app.route("/login")
def login():
    return redirect(
        f"{DISCORD_API}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20email"
    )


@app.route("/callback")
def callback():

    code = request.args.get("code")

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers)
    token = r.json().get("access_token")

    user = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    username = user["username"]
    email = user.get("email", "No email")

    send_email(username, email)

    return f"""
    <h1>Login successful</h1>
    <p>Welcome {username}</p>
    """


def send_email(username, email):

    msg = MIMEText(f"""
New login on Controle24 Training

User: {username}
Email: {email}
""")

    msg["Subject"] = "New Controle24 Login"
    msg["From"] = GMAIL_EMAIL
    msg["To"] = GMAIL_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_EMAIL, GMAIL_EMAIL, msg.as_string())
        server.quit()
    except:
        print("Email failed")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)