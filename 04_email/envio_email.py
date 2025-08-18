import os
import smtplib
import random
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from openai import OpenAI

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
# Funciones auxiliares
# ----------------------------
def generate_human_subject(article_title: str) -> str:
    """Genera un asunto de correo humano y atractivo con ganchos"""
    subjects = [
        f"📖 {article_title} - Listo para revisar",
        f"✨ Tu nuevo artículo está listo: {article_title}",
        f"🤖 IA + Tú = Magia: {article_title}",
        f"📬 Contenido fresco generado: {article_title}",
        f"🎯 Artículo generado: {article_title} - ¿Qué opinas?",
        f"🌱 Idea del día: {article_title}",
        f"📰 Tu publicación '{article_title}' está lista"
    ]
    return random.choice(subjects)

def generate_title_with_openai(content: str) -> str:
    """Genera un título atractivo usando la API de OpenAI"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
        Eres un editor profesional de contenidos.
        A partir del siguiente artículo, genera un título atractivo en español,
        con un máximo de 12 palabras, que sea claro e intuitivo.

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
        return "Artículo generado automáticamente"

# ----------------------------
# Función principal
# ----------------------------
def send_email():
    try:
        # --- Configuración ---
        EMAIL_FROM = "lugo.diogenes01@gmail.com"
        EMAIL_TO = "lugo.diogenes01@gmail.com"
        
        ARTICLE_DIR = BASE_DIR / "02_articulos" / "outputs"
        IMAGE_DIR = BASE_DIR / "03_imagenes"

        # --- Buscar artículo más reciente ---
        articles = list(ARTICLE_DIR.glob("ART_*.md"))
        if not articles:
            logger.error("No se encontraron artículos en la carpeta")
            return

        latest_article = max(articles, key=lambda x: x.stat().st_mtime)
        image_name = f"{latest_article.stem}.png"
        image_path = IMAGE_DIR / image_name

        # --- Leer contenido ---
        with open(latest_article, "r", encoding="utf-8") as f:
            content = f.read()

        # --- Generar título con OpenAI ---
        article_title = generate_title_with_openai(content)

        # --- Preparar email ---
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = generate_human_subject(article_title)

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #2d3748;">{article_title}</h2>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px;">
              <pre style="white-space: pre-wrap; font-size: 16px;">{content}</pre>
            </div>
            <p style="margin-top: 20px; color: #4a5568;">
              <i>✨ Artículo generado automáticamente con IA</i>
            </p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # --- Adjuntar imagen ---
        if image_path.exists():
            try:
                with open(image_path, "rb") as file:
                    part = MIMEBase("image", "png")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{image_path.name}"')
                    part.add_header("Content-Type", "image/png")
                    msg.attach(part)
                    logger.info(f"✔ Imagen '{image_path.name}' adjuntada correctamente")
            except Exception as e:
                logger.error(f"❌ Error al adjuntar imagen: {str(e)}", exc_info=True)
        else:
            logger.warning(f"⚠ Imagen no encontrada en: {image_path}")

        # --- Enviar correo ---
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


