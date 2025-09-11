import os
import json
import logging
import random
import yaml
from datetime import datetime
from openai import OpenAI

# -------------------------
# Configuración de logging
# -------------------------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=os.path.join("logs", "generacion_imagen.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# -------------------------
# Cargar configuración
# -------------------------
with open("03_imagenes/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Parámetros desde config
MODEL_TEXT = config["openai"]["model_text"]
MODEL_IMAGE = config["openai"]["model_image"]
IMAGE_SIZE = config["imagen"]["size"]
IMAGE_QUALITY = config["imagen"]["quality"]
NUM_IMAGES = config["imagen"]["num_images"]
STYLES = config["prompt"]["styles"]
PROMPT_TEMPLATE = config["prompt"]["template"]

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))

# -------------------------
# Función para resumir artículo
# -------------------------
def generar_resumen(texto: str) -> str:
    """
    Usa el modelo de texto para generar un resumen corto (1-2 frases).
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_TEXT,
            messages=[
                {"role": "system", "content": "Eres un experto en comunicación clara."},
                {"role": "user", "content": f"Resume en 1-2 frases el siguiente texto de forma objetiva y clara:\n\n{texto}"}
            ],
            temperature=0.5,
            max_tokens=120,
        )
        resumen = response.choices[0].message.content.strip()
        logging.info(f"Resumen generado: {resumen}")
        return resumen
    except Exception as e:
        logging.error(f"Error al generar resumen: {e}")
        return "Artículo sobre ciencia de datos y aplicaciones de IA en negocios."

# -------------------------
# Función principal
# -------------------------
def main():
    # Rutas
    articulo_path = "02_articulos/articulo_generado.json"
    output_dir = "03_imagenes/outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Leer artículo
    if not os.path.exists(articulo_path):
        logging.error("No se encontró articulo_generado.json")
        return

    with open(articulo_path, "r", encoding="utf-8") as f:
        articulo = json.load(f)

    contenido = articulo.get("contenido", "")
    titulo = articulo.get("titulo", "articulo")

    if not contenido:
        logging.error("El artículo no contiene texto válido")
        return

    # 1. Generar resumen corto
    resumen = generar_resumen(contenido)

    # 2. Seleccionar estilo dinámico
    estilo = random.choice(STYLES)

    # 3. Construir prompt con plantilla
    prompt = PROMPT_TEMPLATE.format(resumen=resumen, estilo=estilo)

    # Guardar prompt en archivo .txt
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_file = os.path.join(output_dir, f"{titulo}_{timestamp}_prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)
    logging.info(f"Prompt guardado en {prompt_file}")

    # 4. Generar imagen
    try:
        result = client.images.generate(
            model=MODEL_IMAGE,
            prompt=prompt,
            size=IMAGE_SIZE,
            quality=IMAGE_QUALITY,
            n=NUM_IMAGES,
        )

        for i, data in enumerate(result.data):
            img_bytes = data.b64_json
            img_path = os.path.join(output_dir, f"{titulo}_{timestamp}_{i+1}.png")
            with open(img_path, "wb") as img_file:
                import base64
                img_file.write(base64.b64decode(img_bytes))
            logging.info(f"Imagen guardada en {img_path}")

    except Exception as e:
        logging.error(f"Error al generar imágenes: {e}")

# -------------------------
# Ejecutar
# -------------------------
if __name__ == "__main__":
    main()





