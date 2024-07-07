from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
    UserMixin,
)

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configuración de MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "KIOya100*"
app.config["MYSQL_DB"] = "cie5"

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = %s AND password = %s",
            (username, password),
        )
        user = cursor.fetchone()
        if user:
            login_user(User(user[0]))
            return redirect(url_for("test"))
    return render_template("login.html")


# Ruta de registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        age = request.form["age"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        gender = request.form["gender"]

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, age, first_name, last_name, gender) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, password, age, first_name, last_name, gender),
        )
        mysql.connection.commit()

        # Optionally, you can automatically log in the user after registration
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]
        login_user(User(user_id))

        return redirect(url_for("test"))

    return render_template("registro.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    if request.method == "POST":
        responses = []
        for i in range(1, 24):
            response = request.form.get(f"q{i}")
            responses.append((current_user.id, i, response))
        cursor = mysql.connection.cursor()
        cursor.executemany(
            "INSERT INTO responses (user_id, question_id, response) VALUES (%s, %s, %s)",
            responses,
        )
        mysql.connection.commit()
        diagnosis = generate_diagnosis(responses)
        cursor.execute(
            "INSERT INTO diagnoses (user_id, diagnosis) VALUES (%s, %s)",
            (current_user.id, diagnosis),
        )
        mysql.connection.commit()
        return redirect(url_for("resultados", diagnosis=diagnosis))
    return render_template("test.html")


@app.route("/resultados")
@login_required
def resultados():
    diagnosis = request.args.get("diagnosis")
    return render_template("resultados.html", diagnosis=diagnosis)


def generate_diagnosis(responses):
    scores = [int(response[2]) for response in responses]
    total_score = sum(scores)
    if total_score < 20:
        return "Salud mental en buen estado"
    elif total_score < 40:
        return "Indicativos leves de problemas de salud mental"
    elif total_score < 60:
        return "Indicativos moderados de problemas de salud mental"
    else:
        return "Indicativos graves de problemas de salud mental"


if __name__ == "__main__":
    app.run(debug=True)
