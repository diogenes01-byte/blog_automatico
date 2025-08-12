import os
import smtplib
import random
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import logging

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
def generate_human_subject(article_title):
    """Genera un asunto de correo humano y atractivo"""
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

# ----------------------------
# Función principal
# ----------------------------
def send_email():
    try:
        # --- Configuración ---
        EMAIL_FROM = "lugo.diogenes01@gmail.com"
        EMAIL_TO = "lugo.diogenes01@gmail.com"
        
        # --- Rutas de archivos ---
        ARTICLE_DIR = BASE_DIR / "02_articulos" / "outputs"
        IMAGE_DIR = BASE_DIR / "03_imagenes"

        # --- Buscar archivos más recientes ---
        articles = list(ARTICLE_DIR.glob("ART_*.md"))
        if not articles:
            logger.error("No se encontraron artículos en la carpeta")
            return

        latest_article = max(articles, key=lambda x: x.stat().st_mtime)
        article_title = latest_article.stem.replace("ART_", "").replace("_", " ")
        image_name = f"{latest_article.stem}.png"
        image_path = IMAGE_DIR / image_name

        # --- Leer contenido ---
        with open(latest_article, "r", encoding="utf-8") as f:
            content = f.read()

        # --- Preparar email ---
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = generate_human_subject(article_title)

        # Cuerpo HTML
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

        # --- Adjuntar imagen (con verificación mejorada) ---
        if image_path.exists():
            logger.info(f"✔ Imagen encontrada: {image_path}")
            try:
                with open(image_path, "rb") as file:
                    part = MIMEBase("image", "png")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    # Header corregido con comillas:
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{image_path.name}"'
                    )
                    part.add_header(
                        "Content-Type",
                        "image/png"
                    )
                    msg.attach(part)
                    logger.info(f"✔ Imagen '{image_path.name}' adjuntada correctamente")
            except Exception as e:
                logger.error(f"❌ Error al adjuntar imagen: {str(e)}", exc_info=True)
        else:
            logger.error(f"❌ Imagen no encontrada en: {image_path}")

        # --- Enviar correo (con SMTP_SSL) ---
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
