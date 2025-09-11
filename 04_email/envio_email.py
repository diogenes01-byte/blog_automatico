import os
import smtplib
import json
import logging
import yaml
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from openai import OpenAI

# ------------------------
# Logging
# ------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "email.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ------------------------
# Cargar configuración
# ------------------------
with open("04_email/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

SMTP_SERVER = config["smtp"]["server"]
SMTP_PORT = config["smtp"]["port"]
EMAIL_USER = config["smtp"]["user"]
EMAIL_PASS = os.getenv(config["smtp"]["password_env"])

RECIPIENTS = config["recipients"]
SUBJECT_PREFIX = config["email"]["subject_prefix"]

ARTICLE_JSON = config["paths"]["article_json"]
ARTICLE_MD = config["paths"]["article_md"]
IMAGES_DIR = config["paths"]["images_dir"]

# ------------------------
# Cliente OpenAI
# ------------------------
client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))

def generar_asunto_ia(titulo, resumen):
    prompt = f"""
    Eres un asistente experto en comunicación.
    Genera un asunto atractivo, profesional y breve para un email de blog
    basado en el título y resumen proporcionados.
    Título: {titulo}
    Resumen: {resumen}
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error al generar asunto con IA: {e}")
        return titulo  # fallback al título

def construir_email():
    # Leer artículo
    try:
        with open(ARTICLE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            titulo = data.get("titulo", "Artículo")
            contenido = data.get("contenido", "")
            resumen = data.get("resumen", "")
    except Exception as e:
        logging.error(f"Error al leer {ARTICLE_JSON}: {e}")
        titulo, contenido, resumen = "Artículo", "", ""

    if not contenido:  # fallback a .md si JSON vacío
        try:
            with open(ARTICLE_MD, "r", encoding="utf-8") as f:
                contenido = f.read()
        except Exception as e:
            logging.error(f"Error al leer {ARTICLE_MD}: {e}")
            contenido = "No se pudo cargar el contenido."

    # Generar asunto híbrido
    asunto_ia = generar_asunto_ia(titulo, resumen)
    asunto_final = f"{SUBJECT_PREFIX} {asunto_ia}"

    # Construir mensaje
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Subject"] = asunto_final

    cuerpo_html = f"""
    <html>
    <body>
        <h2>{titulo}</h2>
        <p>{contenido[:1500]}...</p>
        <p><i>Artículo completo en adjunto</i></p>
    </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo_html, "html"))

    # Adjuntar archivo markdown
    try:
        with open(ARTICLE_MD, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(ARTICLE_MD))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(ARTICLE_MD)}"'
        msg.attach(part)
    except Exception as e:
        logging.warning(f"No se pudo adjuntar {ARTICLE_MD}: {e}")

    # Adjuntar solo la primera imagen (según tu requisito)
    try:
        imgs = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".png")]
        if imgs:
            primera_img = imgs[0]
            with open(os.path.join(IMAGES_DIR, primera_img), "rb") as f:
                img_part = MIMEApplication(f.read(), Name=primera_img)
            img_part["Content-Disposition"] = f'attachment; filename="{primera_img}"'
            msg.attach(img_part)
    except Exception as e:
        logging.warning(f"No se pudo adjuntar imagen: {e}")

    return msg, asunto_final

def enviar_email():
    msg, asunto = construir_email()
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, RECIPIENTS, msg.as_string())
        logging.info(
            f"Correo enviado ✅ | De: {EMAIL_USER} | Para: {RECIPIENTS} | Asunto: {asunto}"
        )
    except Exception as e:
        logging.error(f"Fallo al enviar el correo: {e}")

if __name__ == "__main__":
    enviar_email()








