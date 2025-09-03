import os
import sys
import io
import json
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from openai import OpenAI

# ----------------------------
# Configuración
# ----------------------------
MODELO = "gpt-4"  # o "gpt-3.5-turbo" si prefieres
OPENAI_API_KEY = os.getenv("BLOG_OPENIA_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

TEMPERATURE = 0.7
MAX_TOKENS = 1000
NUM_TEMAS = 10
UMBRAL_TEMAS = 3

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

RUTA_COLA_TEMAS = Path(__file__).parent / "temas_pendientes.json"

# ----------------------------
# Logging
# ----------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(LOG_DIR / "generador_temas.log", maxBytes=5*1024*1024,
                            backupCount=3, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Prompt de generación
# ----------------------------
PROMPT = f"""
Genera una lista de {NUM_TEMAS} temas innovadores sobre Inteligencia Artificial, Machine Learning,
Ciencia de Datos y su aplicación en finanzas, contabilidad y economía.
El objetivo es combinar lo mejor de la tecnología de datos y el mundo financiero.

Requisitos:
1. Temas específicos, técnicos y con aplicación práctica (ej.: "Optimización de carteras de inversión mediante aprendizaje por refuerzo").
2. Evitar temas genéricos como "Qué es IA" o "Introducción a Machine Learning".
3. Un tema por línea, sin numeración ni caracteres especiales.
4. Lenguaje en español.
"""

# ----------------------------
# Funciones
# ----------------------------
def leer_temas_pendientes():
    if RUTA_COLA_TEMAS.exists():
        try:
            with open(RUTA_COLA_TEMAS, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [t.strip() for t in data if t.strip()]
        except json.JSONDecodeError:
            logger.warning("⚠️ JSON corrupto, iniciando con lista vacía.")
    return []

def guardar_temas_pendientes(lista):
    with open(RUTA_COLA_TEMAS, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def generar_con_ia(prompt):
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system",
                 "content": "Eres un experto que propone títulos técnicos innovadores y relevantes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.9
        )
        contenido = response.choices[0].message.content
        logger.info("📥 Respuesta cruda recibida de la API:")
        logger.info(contenido)
        return contenido
    except Exception:
        logger.exception("Error al llamar a OpenAI")
        return None

def generar_temas():
    respuesta = generar_con_ia(PROMPT)
    if not respuesta:
        return []

    temas = []
    for t in respuesta.split("\n"):
        t = t.strip().lstrip("-* ").strip()
        if t:
            temas.append(t)
    return temas[:NUM_TEMAS]

# ----------------------------
# Ejecución principal
# ----------------------------
if __name__ == "__main__":
    logger.info("==== INICIO GENERACIÓN DE TEMAS ====")

    existentes = leer_temas_pendientes()
    logger.info(f"Temas existentes: {len(existentes)}")
    logger.info(f"Lista actual: {existentes}")

    if len(existentes) < UMBRAL_TEMAS:
        logger.info("🔄 Menos de 3 temas, generando nuevos...")
        nuevos = generar_temas()
        if nuevos:
            combinados = existentes + [t for t in nuevos if t not in existentes]
            guardar_temas_pendientes(combinados)
            logger.info(f"✅ Se añadieron {len(nuevos)} nuevos temas.")
            logger.info(f"Lista completa actualizada: {combinados}")
        else:
            logger.warning("⚠️ No se generaron temas.")
    else:
        logger.info("⏸️ Hay suficientes temas, no se generaron nuevos.")

    logger.info("==== FINALIZADO ====")



