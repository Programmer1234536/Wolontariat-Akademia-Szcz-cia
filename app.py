from flask import Flask, request, redirect, session, render_template_string
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, requests
import os

app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "db.db")

RECAPTCHA_SITE = "6LfYMrcsAAAAAFYxxW4GSs5-YssTT1l4touxMdL1"
RECAPTCHA_SECRET = "6LfYMrcsAAAAAOZWz4bj3xbFG3VatfsvFxXTSCq8"

admins = {
    "Gabrysia_M": generate_password_hash("Gabrysia_Mwol.aka.szcz.skala123"),
    "Antoni_L": generate_password_hash("Antoni_Lwol.aka.szcz.skala123"),
    "Kuba_Z": generate_password_hash("Kuba_Lwol.aka.szcz.skala123"),
    "Edyta_Ż": generate_password_hash("Edyta_żwol.aka.szcz.skala123")
}

# ---------- DB ----------
def ensure_tables():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, login TEXT, pass TEXT, status TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY, text TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY, user TEXT, text TEXT)")
    conn.commit()
    conn.close()

def db(q, args=(), one=False):
    ensure_tables()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(q, args)
    conn.commit()
    r = cur.fetchall()
    conn.close()
    return (r[0] if r else None) if one else r

def init():
    ensure_tables()

# Run at module load time so tables exist before the first request,
# regardless of whether the app is started via __main__ or gunicorn.
init()


# ---------- NO CACHE ----------

@app.after_request
def nocache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

# =========================================================
# UI + ANIMACJE (NIC NIE ZMIENIONE)
# =========================================================

STYLE = """
<style>
body{
 margin:0;
 font-family:Segoe UI;
 background:linear-gradient(135deg,#fff9c4,#90caf9);
 display:flex;
 flex-direction:column;
 min-height:100vh;
}

.card{
 animation:fadeIn .35s ease-in-out;
}

@keyframes fadeIn{
 from{opacity:0; transform:translateY(8px);}
 to{opacity:1; transform:translateY(0);}
}

header{
 background:linear-gradient(135deg,#fdd835,#2196f3);
 color:white;
 text-align:center;
 padding:25px;
 box-shadow:0 4px 20px rgba(0,0,0,0.2);
}

header img{
 width:70px;
 height:70px;
 object-fit:contain;
 display:block;
 margin:0 auto 10px;
}

nav a{
 background:white;
 padding:10px 16px;
 border-radius:12px;
 text-decoration:none;
 margin:5px;
 display:inline-block;
 color:#1976d2;
 font-weight:600;
}

main{
 flex:1;
 max-width:900px;
 margin:auto;
 padding:20px;
}

.card{
 background:white;
 padding:20px;
 border-radius:18px;
 margin:10px 0;
 box-shadow:0 8px 25px rgba(0,0,0,0.12);
}

input,button{
 width:100%;
 padding:12px;
 margin:8px 0;
 border-radius:10px;
 border:1px solid #ccc;
}

button{
 background:#1976d2;
 color:white;
 border:none;
 cursor:pointer;
}

.small-btn{
 padding:8px 12px;
 background:#1976d2;
 color:white;
 border-radius:10px;
 text-decoration:none;
 margin-right:5px;
}

.small-btn.red{background:#e53935;}
</style>
"""

# ---------- HOME ----------
@app.route("/")
def home():
    news = db("SELECT * FROM news")

    news_html = ""
    if news:
        for n in news:
            news_html += f"<div class='card'>{n[1]}</div>"
    else:
        news_html = "<div class='card'>Brak aktualności 📭</div>"

    return render_template_string(f"""
    {STYLE}
    <header>
        <img src="/static/logo.png">
        <h1>🎓 Akademia Szczęścia</h1>
        <nav>
            <a href="/">Start</a>
            <a href="/login">Zaloguj</a>
            <a href="/register">Rejestracja</a>
            <a href="/admin_login">Organizator</a>
        </nav>
    </header>
    <title>Wolontariat Szkolny Akademia Szczęścia</title>

    <main>
        <div class="card">Nasza misja❤️: Naszą misją jest pomaganie innym, prowadzimy korepetycje dla młodszcych uczniów, organizujemy akcje charetatywne, i wiele więcej! </div>

         <div class="card">Przypominamy że uczniowie Niepublicznej Szkoły Postawowej Skala z odziałami itegracyjnymi jako jedyni mogą zgłosić się na wolontariusza(prośby z poza szkoły są usuwane)</div>

        <div class="card">
            <b>📢 Aktualności</b>
        </div>

        {news_html}
    </main>
    """)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        token = request.form.get("g-recaptcha-response")

        verify = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SECRET, "response": token}
        ).json()

        if not verify.get("success"):
            return "reCAPTCHA error"

        db("INSERT INTO users(login,pass,status) VALUES (?,?,?)",
           (request.form["login"],
            generate_password_hash(request.form["pass"]),
            "pending"))

        return redirect("/login")

    return render_template_string(f"""
    {STYLE}
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>

    <header>
        <img src="/static/logo.png">
        <h1>Rejestracja</h1>
    </header>

    <main>
        <div class="card">
            <form method="POST">
                <input name="login" placeholder="Login">
                <input name="pass" type="password" placeholder="Hasło">
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE}"></div>
                <button>Zarejestruj</button>
            </form>
        </div>
    </main>
    """)

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = db("SELECT * FROM users WHERE login=?", (request.form["login"],), one=True)

        if not user:
            return redirect("/login")
        if not check_password_hash(user[2], request.form["pass"]):
            return redirect("/login")
        if user[3] != "accepted":
            return "Czeka na akceptację"

        session["user"] = user[1]
        return redirect("/panel")

    return render_template_string(f"""
    {STYLE}
    <header><img src="/static/logo.png"><h1>Logowanie</h1></header>

    <main>
        <div class="card">
            <form method="POST">
                <input name="login" placeholder="Login">
                <input name="pass" type="password" placeholder="Hasło">
                <button>Zaloguj</button>
            </form>
        </div>
    </main>
    """)

# ---------- ADMIN LOGIN ----------
@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form["login"] in admins and check_password_hash(
            admins[request.form["login"]], request.form["pass"]):

            session["admin"] = request.form["login"]
            return redirect("/admin")

        return redirect("/admin_login")

    return render_template_string(f"""
    {STYLE}
    <header><h1>Organizator</h1></header>

    <main>
        <div class="card">
            <form method="POST">
                <input name="login" placeholder="Login">
                <input name="pass" type="password" placeholder="Hasło">
                <button>Zaloguj</button>
            </form>
        </div>
    </main>
    """)

# ---------- ADMIN PANEL (FIXED + ADD NEWS) ----------
@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/admin_login")

    users = db("SELECT * FROM users WHERE status='pending'")
    news = db("SELECT * FROM news")

    users_html = ""
    if users:
        for u in users:
            users_html += f"""
            <div class="card">
                {u[1]}<br>
                <a class="small-btn" href="/accept/{u[0]}">Akceptuj</a>
                <a class="small-btn red" href="/reject/{u[0]}">Usuń</a>
            </div>
            """
    else:
        users_html = "<div class='card'>Brak nowych użytkowników 👤</div>"

    news_html = ""
    if news:
        for n in news:
            news_html += f"""
            <div class="card">
                {n[1]}<br>
                <a class="small-btn red" href="/delete_news/{n[0]}">Usuń</a>
            </div>
            """
    else:
        news_html = "<div class='card'>Brak aktualności 📭</div>"

    return render_template_string(f"""
    {STYLE}
    <header>
        <img src="/static/logo.png">
        <h1>Organizator panel</h1>
    </header>

    <main>

        <div class="card">
            <b>➕ Dodaj aktualność</b>
            <form method="POST" action="/add_news">
                <input name="text" placeholder="Treść aktualności">
                <button>Dodaj</button>
            </form>
        </div>

        <div class="card">
            <b>📢 Aktualności</b>
            {news_html}
        </div>

        <div class="card">
            <b>👤 Użytkownicy</b>
            {users_html}
        </div>

    </main>
    """)

# ---------- NEWS ACTIONS ----------
@app.route("/add_news", methods=["POST"])
def add_news():
    if "admin" not in session:
        return redirect("/admin_login")
    db("INSERT INTO news(text) VALUES (?)", (request.form["text"],))
    return redirect("/admin")

@app.route("/delete_news/<int:id>")
def delete_news(id):
    if "admin" not in session:
        return redirect("/admin_login")
    db("DELETE FROM news WHERE id=?", (id,))
    return redirect("/admin")

# ---------- USERS ----------
@app.route("/accept/<int:id>")
def accept(id):
    db("UPDATE users SET status='accepted' WHERE id=?", (id,))
    return redirect("/admin")

@app.route("/reject/<int:id>")
def reject(id):
    db("UPDATE users SET status='rejected' WHERE id=?", (id,))
    return redirect("/admin")

# ---------- START ----------
if __name__ == "__main__":
    init()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
