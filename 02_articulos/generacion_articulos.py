import os
import json
import logging
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# ----------------------------
# Configuración de rutas
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
TEMAS_PATH = BASE_DIR / "01_temas" / "temas_pendientes.json"
ARTICULOS_DIR = BASE_DIR / "02_articulos" / "outputs"

ARTICULOS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "generador_articulos.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Configuración de OpenAI
# ----------------------------
client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))
MODELO = "gpt-4o"
TEMPERATURE = 0.7

# ----------------------------
# Selección de tema
# ----------------------------
def seleccionar_tema():
    """Obtiene el primer tema del JSON, lo elimina de la lista y re-guarda."""
    if not TEMAS_PATH.exists():
        logger.error("❌ El archivo de temas pendientes no existe.")
        return None

    try:
        with open(TEMAS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            temas = data.get("temas", [])

        if not temas:
            logger.warning("⚠️ No hay temas pendientes disponibles.")
            return None

        tema = temas.pop(0)
        logger.info(f"📌 Tema seleccionado: {tema}")

        # Guardar JSON actualizado
        with open(TEMAS_PATH, "w", encoding="utf-8") as f:
            json.dump({"temas": temas}, f, ensure_ascii=False, indent=2)

        return tema
    except Exception as e:
        logger.error(f"Error al procesar la cola de temas: {e}", exc_info=True)
        return None

# ----------------------------
# Generación de artículo
# ----------------------------
def generar_articulo(tema: str):
    try:
        prompt = f"""
Actúa como redactor técnico profesional especializado en divulgación tecnológica y científica,
con habilidad para combinar rigor técnico y humor inteligente, manteniendo al lector enganchado.

Escribe un artículo técnico en español de entre 1200 y 1500 palabras sobre {tema}, en narrativa continua,
sin títulos o subtítulos explícitos, que fluya con transiciones naturales. 
Incluye historia inicial, explicaciones técnicas con analogías, casos de uso, predicciones a 2-5 años,
citas de expertos y conclusión clara. Mantén tono atractivo y un 20% de humor.
"""
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un ingeniero senior que escribe artículos técnicos con humor inteligente en español."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=6000
        )
        return response.choices[0].message.content.strip().strip('"')  # elimina comillas sobrantes
    except Exception as e:
        logger.error(f"Error al generar artículo: {e}", exc_info=True)
        return None

# ----------------------------
# Guardado
# ----------------------------
def guardar_articulo(tema, contenido):
    try:
        fecha = datetime.now().strftime("%d-%m-%y")
        palabras_clave = [
            p for p in tema.lower().split()
            if p not in ["de", "para", "en", "y", "con", "como"]
            and len(p) > 3 and p.isalpha()
        ][:3]

        nombre_archivo = ARTICULOS_DIR / f"ART_{fecha}_{'_'.join(palabras_clave)}.md"

        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(contenido)

        logger.info(f"✅ Artículo guardado en {nombre_archivo}")
        logger.info(f"📝 Longitud aproximada: {len(contenido.split())} palabras")
        return nombre_archivo
    except Exception as e:
        logger.error(f"Error al guardar artículo: {e}", exc_info=True)
        return None

# ----------------------------
# Ejecución principal
# ----------------------------
if __name__ == "__main__":
    logger.info("==== INICIO GENERACIÓN DE ARTÍCULO ====")

    tema = seleccionar_tema()
    if not tema:
        logger.error("🚫 No se pudo seleccionar un tema válido.")
        exit(1)

    articulo = generar_articulo(tema)
    if not articulo:
        logger.error("❌ Falló la generación del artículo.")
        exit(1)

    guardar_articulo(tema, articulo)
    logger.info("==== FINALIZADO ====")


