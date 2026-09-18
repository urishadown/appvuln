from flask import Flask, request, make_response
import os

app = Flask(__name__)

@app.route("/")
def index():
    response = """
    <html>
    <head>
        <title>Aplicação Vulnerável - Nikto Lab</title>
    </head>
    <body>
        <h1>Laboratório Nikto</h1>

        <h2>Endpoints</h2>

        <ul>
            <li><a href="/admin">Admin</a></li>
            <li><a href="/backup">Backup</a></li>
            <li><a href="/server-status">Server Status</a></li>
            <li><a href="/debug">Debug</a></li>
            <li><a href="/robots.txt">robots.txt</a></li>
        </ul>

        <form method="POST" action="/login">
            <input name="username" placeholder="Usuário">
            <input name="password" type="password" placeholder="Senha">
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """

    response = make_response(response)

    # Headers de segurança propositalmente ausentes.

    return response


@app.route("/admin")
def admin():
    return """
    <h1>Área Administrativa</h1>
    <p>Esta área deveria exigir autenticação.</p>
    <p>Usuário administrativo: admin</p>
    """


@app.route("/backup")
def backup():
    return """
    <h1>Backup</h1>
    <pre>
    database_user=admin
    database_password=SuperSecret123
    api_key=LAB-123456789
    </pre>
    """


@app.route("/server-status")
def server_status():
    return """
    <h1>Server Status</h1>
    <p>Server version: Apache/2.4.49</p>
    <p>Python application running in development mode.</p>
    """


@app.route("/robots.txt")
def robots():
    return """
User-agent: *
Disallow: /admin
Disallow: /backup
Disallow: /server-status
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            return "Login realizado."

        return "Usuário ou senha inválidos."

    return "Login"


@app.route("/debug")
def debug():
    return {
        "debug": True,
        "environment": os.environ.get("APP_ENV", "development"),
        "database": "mysql://admin:password@db/app"
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )
 
