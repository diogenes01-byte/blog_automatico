import os
import smtplib
import logging
import random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
from dotenv import load_dotenv

# ----------------------------
# Configuración inicial
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "lugo.diogenes01@gmail.com"  
RECEIVER_EMAIL = "lugo.diogenes01@gmail.com"  
SMTP_PASSWORD = os.getenv("GMAIL_KEY")


# ----------------------------
# Generar título con OpenAI
# ----------------------------
def generate_title_with_openai(content: str) -> str:
    """Genera un título atractivo basado en el contenido del artículo"""
    try:
        client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))

        prompt = f"""
        Eres un editor profesional. 
        Lee el siguiente artículo y genera un título atractivo en español, 
        máximo 12 palabras, que resuma el tema central de forma clara e intuitiva.
        No uses frases genéricas como 'Artículo generado automáticamente'. 
        Devuelve solo el título, sin comillas ni adornos.

        Artículo:
        {content}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en redacción de títulos periodísticos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=40,
            temperature=0.7
        )

        title = response.choices[0].message.content.strip()
        logger.info(f"✔ Título generado con OpenAI: {title}")
        return title

    except Exception as e:
        logger.error(f"❌ Error al generar título con OpenAI: {str(e)}", exc_info=True)
        return "Título no disponible"


# ----------------------------
# Asunto del correo
# ----------------------------
def generate_human_subject(article_title: str) -> str:
    """Genera asunto con estructura: gancho + título + emoji"""
    ganchos = [
        "🚀 Descubre:",
        "🔥 No te pierdas:",
        "✨ Lo último en IA:",
        "📊 Análisis exclusivo:",
        "💡 Ideas frescas:",
        "🤖 Innovación al día:",
        "🌍 Tendencias globales:"
    ]
    emojis_finales = ["🚀", "🔥", "✨", "📊", "💡", "🤖", "🌍"]

    gancho = random.choice(ganchos)
    emoji = random.choice(emojis_finales)

    # Estructura final
    return f"{gancho} {article_title} {emoji}"


# ----------------------------
# Envío de email
# ----------------------------
def send_email(article_content: str):
    """Envía el artículo generado por correo con un asunto atractivo"""

    # 1. Generar título real del artículo con IA
    article_title = generate_title_with_openai(article_content)

    # 2. Construir asunto final
    subject = generate_human_subject(article_title)

    # 3. Crear cuerpo del correo
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(article_content, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"📨 Correo enviado con asunto: {subject}")
    except Exception as e:
        logger.error(f"❌ Error enviando correo: {str(e)}", exc_info=True)


# ----------------------------
# Ejecución directa (test)
# ----------------------------
if __name__ == "__main__":
    test_content = """
    La inteligencia artificial está revolucionando el análisis de datos en pequeñas y medianas empresas. 
    Desde herramientas de predicción hasta automatización de procesos, la IA permite tomar mejores decisiones 
    y optimizar recursos.
    """
    send_email(test_content)



