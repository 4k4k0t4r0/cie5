from flask import Flask, render_template, request, redirect, url_for, send_file
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


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# Ruta para servir archivos estáticos (en este caso, indicator.png)
@app.route("/templates/<filename>")
@login_required
def serve_file(filename):
    return send_file(os.path.join(app.root_path, "templates", filename))


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Definir tu API key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

import os

# Obtén la ruta absoluta del directorio actual del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Construye la ruta completa al archivo config.json
CLIENTE = os.path.join(BASE_DIR, "config", "config.json")

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
    "Pregunta 1": "¿Poco interés o satisfacción en hacer cosas?",
    "Pregunta 2": "¿Sentirse bajo de ánimo, deprimido o desesperanzado?",
    "Pregunta 3": "¿Sentirse más irritado, malhumorado o enfadado que normalmente?",
    "Pregunta 4": "¿Dormir menos de lo normal pero todavía con mucha energía?",
    "Pregunta 5": "¿Empezar más proyectos de lo normal o hacer cosas más arriesgadas de lo normal?",
    "Pregunta 6": "¿Sentirse nervioso, ansioso, preocupado o al límite?",
    "Pregunta 7": "¿Sentir pánico o estar atemorizado?",
    "Pregunta 8": "¿Evitar situaciones que le ponen nervioso?",
    "Pregunta 9": "¿Dolores o molestias inexplicados (p. ej., cabeza, espalda, articulaciones, abdomen, piernas)?",
    "Pregunta 10": "¿Sentir que sus enfermedades no se toman lo suficientemente en serio?",
    "Pregunta 11": "¿Tener pensamientos de dañarse a sí mismo?",
    "Pregunta 12": "¿Oír cosas que otras personas no podrían oír, como voces, incluso cuando no hay nadie alrededor?",
    "Pregunta 13": "¿Sentir que alguien podría oír sus pensamientos o que usted podría escuchar lo que otra persona estaba pensando?",
    "Pregunta 14": "¿Problemas de sueño que afectan a su calidad de sueño en general?",
    "Pregunta 15": "¿Problemas con la memoria (p. ej., aprender nueva información) o con la ubicación (p. ej., encontrar el camino a casa)?",
    "Pregunta 16": "¿Pensamientos desagradables, necesidades urgentes o imágenes repetidas en su cabeza?",
    "Pregunta 17": "¿Sentirse impulsado a realizar ciertos comportamientos o actos mentales una y otra vez?",
    "Pregunta 18": "¿Sentir que no es realmente usted mismo o que está muy separado de sí mismo?",
    "Pregunta 19": "¿No saber quién es realmente o qué es lo que quiere de la vida?",
    "Pregunta 20": "¿No sentirse cercano a otras personas o no disfrutar de sus relaciones con ellas?",
    "Pregunta 21": "¿Tomar al menos cuatro bebidas de cualquier tipo de alcohol en un solo día?",
    "Pregunta 22": "¿Fumar cigarrillos, puros o en pipa, o usar tabaco en polvo, o masticar tabaco?",
    "Pregunta 23": "¿Usar una de las medicinas siguientes A SU MANERA, esto es, sin la prescripción de un médico, en mayores cantidades o más tiempo de lo prescrito?",
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
    # Ruta del archivo indicator.png
    indicator_path = os.path.join(app.template_folder, "indicator.png")

    # Verificar si el archivo existe y eliminarlo
    if os.path.exists(indicator_path):
        os.remove(indicator_path)

    logout_user()

    return redirect(url_for("login"))


@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    if request.method == "POST":
        responses = []
        total_score = 0  # Inicializa el total_score
        question_11_value = None  # Variable para almacenar el valor de la pregunta 11
        for i in range(1, 24):
            response = request.form.get(f"q{i}")
            responses.append((current_user.id, i, response))
            if i == 11:
                question_11_value = response  # Captura el valor de la pregunta 11
                # Ajusta el puntaje según la respuesta de la pregunta 11
                if response == "1":
                    total_score += 92
                elif response == "2":
                    total_score += 92 * 2
                elif response == "3":
                    total_score += 92 * 3
                elif response == "4":
                    total_score += 92 * 4
            else:
                total_score += int(response)  # Suma el puntaje de cada respuesta

        cursor = mysql.connection.cursor()
        cursor.executemany(
            "INSERT INTO responses (user_id, question_id, response) VALUES (%s, %s, %s)",
            responses,
        )
        mysql.connection.commit()
        diagnosis = generate_diagnosis(responses)
        recommendations = generate_recommendations(diagnosis)
        # Envía el correo de alerta con el diagnóstico y el valor de la pregunta 11
        send_alert_email(diagnosis, question_11_value)
        # Generar indicador y guardar la imagen
        plot_indicator(total_score, diagnosis, question_11_value)
        # Directly pass recommendations to the resultados route
        return redirect(
            url_for("resultados", diagnosis=diagnosis, recommendations=recommendations)
        )
    return render_template("test.html")


@app.route("/resultados")
@login_required
def resultados():
    diagnosis = request.args.get("diagnosis")
    recommendations = request.args.get("recommendations")

    # Obtener información del usuario para mostrar en la página de resultados
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT first_name, last_name, age, gender FROM users WHERE id = %s",
        (current_user.id,),
    )
    user_info = cursor.fetchone()
    user = {
        "first_name": user_info[0],
        "last_name": user_info[1],
        "age": user_info[2],
        "gender": user_info[3],
    }

    return render_template(
        "resultados.html",
        diagnosis=diagnosis,
        recommendations=recommendations,
        user=user,
    )


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
            "content": "Eres un profesional médico especializado en diagnósticos basados en el DSM-5. Tu tarea es analizar las respuestas del paciente en base a las preguntas y proporcionar un diagnóstico detallado y coherente basado en los criterios del DSM-5.",
        },
        {
            "role": "user",
            "content": f"Estas son las respuestas del paciente al cuestionario DSM-5:\n\n{responses_text}\n\nCon base en estas respuestas, proporciona un diagnóstico preciso y conciso de según los criterios del DSM-5.",
        },
    ]

    # Llamar al API de OpenAI para obtener un diagnóstico más detallado
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=320,  # Ajuste de tokens para asegurar la completitud
            temperature=0.7,  # Ajustar la temperatura para obtener un diagnóstico más consistente
        )
        diagnosis = response["choices"][0]["message"]["content"].strip()
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        diagnosis = "No se pudo generar un diagnóstico en este momento debido a un error de la API de OpenAI."
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        diagnosis = "No se pudo generar un diagnóstico en este momento debido a un error inesperado."

    return diagnosis


def generate_recommendations(diagnosis):
    # Crear el mensaje para enviar al modelo de OpenAI
    messages = [
        {
            "role": "system",
            "content": "Eres un asistente médico que proporciona recomendaciones basadas en diagnósticos DSM-5. Proporciona un máximo de 4 recomendaciones en un formato de lista con un salto de línea entre cada recomendación.",
        },
        {
            "role": "user",
            "content": f"El diagnóstico del paciente es el siguiente:\n{diagnosis}\nProporciona un máximo de 4 recomendaciones basadas en este diagnóstico. Asegúrate de incluir sugerencias como mirar series, hacer actividad física y otras terapias adecuadas.",
        },
    ]

    # Llamar al API de OpenAI para obtener recomendaciones
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,  # Ajuste de tokens para asegurar respuestas concisas
            temperature=0.7,
        )
        recommendations = response["choices"][0]["message"]["content"].strip()
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        recommendations = "No se pudieron generar recomendaciones en este momento debido a un error de la API de OpenAI."
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        recommendations = "No se pudieron generar recomendaciones en este momento debido a un error inesperado."

    return recommendations


def send_alert_email(diagnosis, question_11_value):
    mimeMessage = MIMEMultipart()
    mimeMessage["subject"] = "Alerta de Diagnóstico Grave"
    emailMsg = f"Se ha detectado un diagnóstico de gravedad:\n{diagnosis}\n\nValor de la pregunta 11: {question_11_value}"
    mimeMessage["to"] = "actionx100pre@gmail.com"

    mimeMessage.attach(MIMEText(emailMsg, "plain"))

    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

    message = (
        service.users().messages().send(userId="me", body={"raw": raw_string}).execute()
    )
    print("Se ha enviado correctamente el correo de alerta.")


import matplotlib.pyplot as plt


def plot_indicator(total_score, diagnosis, question_11_value):

    # Asegurarse de que el total_score no supere el máximo posible (92 en tu caso)
    total_score = min(total_score, 480)
    # Determinar el estado según el total_score
    if total_score <= 30:
        position = total_score / 30 * 100
        estado = "Leve"
        color = "green"
    elif total_score <= 60:
        position = ((total_score - 30) / 30 * 100) + 33
        estado = "Moderado"
        color = "yellow"
    else:
        position = ((total_score - 60) / 32 * 100) + 66
        estado = "Grave"
        color = "red"

        # Si el estado es "Grave", envía el correo de alerta
    if estado == "Grave":
        send_alert_email(diagnosis, question_11_value)

        # Crear la gráfica con un tamaño más largo horizontalmente
    fig, ax = plt.subplots(figsize=(8, 3))  # Ajusta el ancho a 8 pulgadas

    # Dibuja el indicador
    ax.barh([0], [500], color="lightgrey", height=0.3)
    ax.barh([0], [position], color=color, height=0.3)
    ax.set_xlim(0, 500)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])

    # Marcador en forma de aguja
    ax.plot(
        [position, position], [-0.15, 0.15], color="black", lw=2
    )  # Ajusta las coordenadas y el grosor

    # Añadir texto
    ax.text(0, 0, f"{int(total_score)} puntos", ha="center", va="center", fontsize=14)
    ax.text(
        250,
        -0.8,
        "Salud Mental",  # Cambia aquí el nombre del indicador
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )
    ax.text(
        position,
        -0.4,
        estado,
        ha="center",
        va="center",
        fontsize=14,
        color=color,
        fontweight="bold",
    )

    # Quitar bordes
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Guardar la gráfica como imagen PNG en la carpeta templates
    plt.savefig("templates/indicator.png", bbox_inches="tight")

    # Cerrar la figura para liberar recursos
    plt.close()


if __name__ == "__main__":
    app.run(debug=True)
