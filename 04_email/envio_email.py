import os
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

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

def send_email():
    # --- Configuración del correo ---
    EMAIL_FROM = "lugo.diogenes01@gmail.com"
    EMAIL_TO = "lugo.diogenes01@gmail.com"
    EMAIL_PASSWORD = os.getenv("GMAIL_KEY")  # Usa variable de entorno

    # --- Rutas de archivos ---
    ARTICLE_PATH = os.path.join("articles", "outputs", "article_output.md")
    IMAGE_PATH = os.path.join("imagenes", "article_image.png")

    # --- Leer contenido del artículo ---
    try:
        with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extraer título y cuerpo
        title = content.split('\n')[0].strip()
        body_content = "\n".join(content.split('\n')[1:])
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {ARTICLE_PATH}")
        return

    # --- Preparar email ---
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = generate_human_subject(title)  # Asunto dinámico
    
    # Cuerpo en HTML
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #2d3748;">{title}</h2>
        <div style="background: #f7fafc; padding: 20px; border-radius: 8px;">
          <pre style="white-space: pre-wrap; font-size: 16px;">{body_content}</pre>
        </div>
        <p style="margin-top: 20px; color: #4a5568;">
          <i>✨ Artículo generado automáticamente con IA</i>
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    # --- Adjuntar imagen ---
    if os.path.exists(IMAGE_PATH):
        try:
            with open(IMAGE_PATH, "rb") as file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=articulo-{os.path.basename(IMAGE_PATH)}"
                )
                msg.attach(part)
                print("📎 Imagen adjuntada correctamente")
        except Exception as e:
            print(f"❌ Error adjuntando imagen: {str(e)}")
    else:
        print(f"⚠️ Imagen no encontrada en {IMAGE_PATH}")

    # --- Enviar correo ---
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            print(f"✅ Correo enviado con asunto: '{msg['Subject']}'")
    except Exception as e:
        print(f"❌ Error enviando correo: {str(e)}")
        if "application-specific password" in str(e).lower():
            print("💡 Solución: Genera una 'contraseña de aplicación' en tu cuenta de Google")

if __name__ == "__main__":
    send_email()