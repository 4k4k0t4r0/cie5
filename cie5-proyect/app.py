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
from dotenv import load_dotenv
import os
import openai
from Google import Create_Service
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Definir tu API key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuración de Gmail API
CLIENTE = "cie5-proyect/config/config.json"  # Ajusta la ruta según sea necesario
API_NAME = "gmail"
API_VERSION = "v1"
SCOPES = ["https://mail.google.com/"]

service = Create_Service(CLIENTE, API_NAME, API_VERSION, SCOPES)

# Definir las descripciones de los puntajes según el DSM-5
score_descriptions = {
    "0": "Nada en ningún momento",
    "1": "Algo raro, menos de un día o dos",
    "2": "Leve, varios días",
    "3": "Moderado, más de la mitad de los días",
    "4": "Grave, casi cada día",
}

# Mapeo de preguntas a dominios DSM-5
question_domains = {
    "Pregunta 1": "Depresión",
    "Pregunta 2": "Ira",
    "Pregunta 3": "Manía",
    "Pregunta 4": "Ansiedad",
    "Pregunta 5": "Síntomas somáticos",
    "Pregunta 6": "Ideas suicidas",
    "Pregunta 7": "Psicosis",
    "Pregunta 8": "Problemas de sueño",
    "Pregunta 9": "Memoria",
    "Pregunta 10": "Pensamientos y comportamientos repetitivos",
    "Pregunta 11": "Disociación",
    "Pregunta 12": "Funcionamiento de la personalidad",
    "Pregunta 13": "Consumo de sustancias",
}

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
    # Obtener respuestas y convertir a texto descriptivo
    scores = [int(response[2]) for response in responses]
    responses_text = "\n".join(
        [
            f"{question_domains.get(f'Pregunta {i}', 'Dominio desconocido')}: {score_descriptions[str(score)]}"
            for i, score in enumerate(scores, start=1)
        ]
    )

    # Crear el mensaje para enviar al modelo de OpenAI
    messages = [
        {
            "role": "system",
            "content": "Eres un asistente médico que proporciona diagnósticos basados en el DSM-5.",
        },
        {
            "role": "user",
            "content": f"Estas son las respuestas del paciente al cuestionario DSM-5:\n{responses_text}\nProporciona un diagnóstico basado en estas respuestas.",
        },
    ]

    # Llamar al API de OpenAI para obtener un diagnóstico más detallado
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        diagnosis = response["choices"][0]["message"]["content"].strip()
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        diagnosis = "No se pudo generar un diagnóstico en este momento debido a un error de la API de OpenAI."
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        diagnosis = "No se pudo generar un diagnóstico en este momento debido a un error inesperado."

    # Enviar correo de alerta si el diagnóstico es grave
    if "Grave" in responses_text:
        send_alert_email(diagnosis)
        
    return diagnosis

def send_alert_email(diagnosis):
    mimeMessage = MIMEMultipart()
    mimeMessage["subject"] = "Alerta de Diagnóstico Grave"
    emailMsg = f"Se ha detectado un diagnóstico de gravedad:\n{diagnosis}"
    mimeMessage["to"] = "keffo.stf@gmail.com"

    mimeMessage.attach(MIMEText(emailMsg, "plain"))

    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

    message = service.users().messages().send(userId="me", body={"raw": raw_string}).execute()
    print("Se ha enviado correctamente el correo de alerta.")

if __name__ == "__main__":
    app.run(debug=True)
