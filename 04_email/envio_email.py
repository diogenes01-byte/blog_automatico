import os
import smtplib
import random
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import logging
from openai import OpenAI
import markdown  # Necesario para convertir Markdown a HTML

# ----------------------------
# Configuración de logging
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "04_enviar_email.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Cliente OpenAI
# ----------------------------
client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))

# ----------------------------
# Lista de ganchos
# ----------------------------
HOOKS = [
    "🚀 Descubre:", "🔥 No te pierdas:", "💡 Aprende sobre:",
    "✨ Novedad:", "📊 Datos reveladores:", "📖 Lectura recomendada:",
    "🎯 Clave del día:", "🤖 Tecnología en acción:", "🌍 Perspectiva global:"
]
EMOJIS = ["🚀", "🔥", "💡", "✨", "📊", "📖", "🎯", "🤖", "🌍"]

# ----------------------------
# Generar asunto inteligente
# ----------------------------
def generate_subject_from_article(content: str) -> str:
    try:
        logger.info("Generando título con OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que crea títulos llamativos y concisos basados en artículos. Devuelve solo un título breve."
                },
                {"role": "user", "content": content[:1500]}
            ],
            max_tokens=30,
            temperature=0.7,
        )
        ai_title = response.choices[0].message.content.strip()

        hook = random.choice(HOOKS)
        emoji = random.choice(EMOJIS)
        subject = f"{hook} {ai_title} {emoji}"
        return subject
    except Exception as e:
        logger.error(f"❌ Error generando asunto con IA: {str(e)}", exc_info=True)
        return "📬 Artículo generado automáticamente"

# ----------------------------
# Función principal
# ----------------------------
def send_email():
    try:
        EMAIL_FROM = "lugo.diogenes01@gmail.com"
        EMAIL_TO = "lugo.diogenes01@gmail.com"

        ARTICLE_PATH = BASE_DIR / "02_articulos" / "articulo_generado.json"
        IMAGE_DIR = BASE_DIR / "03_imagenes"

        if not ARTICLE_PATH.exists():
            logger.error("No se encontró el archivo de artículo")
            return

        # Leer JSON y extraer contenido
        with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        article_title = data.get("titulo", "Artículo generado")
        content_md = data.get("contenido", "")

        # Convertir Markdown a HTML
        content_html = markdown.markdown(content_md, extensions=['extra', 'nl2br'])

        image_name = f"{ARTICLE_PATH.stem}.png"
        image_path = IMAGE_DIR / image_name

        subject = generate_subject_from_article(content_md)

        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = subject

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; text-align: justify;">
            <h2 style="color:#2d3748;">{article_title}</h2>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px;">
              {content_html}
            </div>
            <p style="margin-top: 20px; color: #4a5568; text-align: center;">
              <i>✍️ Redactado por Chart G. PT, tu redactor de IA de confianza</i>
            </p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # Adjuntar imagen si existe
        if image_path.exists():
            logger.info(f"✔ Imagen encontrada: {image_path}")
            with open(image_path, "rb") as file:
                part = MIMEBase("image", "png")
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{image_path.name}"'
                )
                msg.attach(part)
                logger.info(f"✔ Imagen '{image_path.name}' adjuntada correctamente")
        else:
            logger.warning(f"⚠ Imagen no encontrada en: {image_path}")

        logger.info("Conectando con servidor SMTP...")
        GMAIL_KEY = os.getenv("GMAIL_KEY")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, GMAIL_KEY)
            server.send_message(msg)
            logger.info("✅ Correo enviado exitosamente")

    except smtplib.SMTPAuthenticationError:
        logger.error("""
        ❌ Error de autenticación. Verifica:
        1. Que la verificación en 2 pasos esté ACTIVADA
        2. Que hayas generado una CONTRASEÑA DE APLICACIÓN
        3. Que estés usando la contraseña de aplicación (16 caracteres)
        """)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)

# ----------------------------
# Ejecución
# ----------------------------
if __name__ == "__main__":
    logger.info("==== INICIO DE ENVÍO ====")
    send_email()
    logger.info("==== PROCESO COMPLETADO ====")






