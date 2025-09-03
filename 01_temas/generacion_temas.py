import os
import logging
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import json

# ----------------------------
# Configuración
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
TEMAS_JSON_PATH = BASE_DIR / "01_temas" / "titulos.json"
NUM_TEMAS_TOTAL = 10  # Número total de temas que siempre queremos mantener
MODELO = "gpt-4"
TEMPERATURE = 0.7
MAX_TOKENS = 1000

LOG_DIR.mkdir(exist_ok=True)

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "generador_temas.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Configuración de OpenAI
# ----------------------------
client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))

# ----------------------------
# Prompt de generación de temas
# ----------------------------
def generar_prompt(cantidad):
    return f"""
Genera {cantidad} temas altamente innovadores y orientados al futuro para artículos técnicos sobre:
- Inteligencia Artificial avanzada y aplicada
- Ciencia de Datos de nueva generación
- Ingeniería de Machine Learning y MLOps
- Modelos fundacionales, agentes autónomos y sistemas multiagente
- Data mesh, data fabric y arquitecturas descentralizadas de datos
- Explainable AI (XAI), auditoría algorítmica y confianza en IA
- Edge AI, análisis en tiempo real y procesamiento en el dispositivo
- IA generativa para descubrimientos científicos y simulaciones
- Integración de IA con computación cuántica y HPC
- Automatización cognitiva y toma de decisiones autónoma
- Aplicaciones de IA y datos en finanzas, economía y contabilidad

Requisitos:
1. Temas concretos, con aplicación práctica o técnica detallada.
2. Evitar temas genéricos como 'Qué es Machine Learning'.
3. Evitar salud, medicina o tópicos repetidos.
4. Formato: un tema por línea, sin numeración ni caracteres especiales.
"""

# ----------------------------
# Función para generar temas con IA
# ----------------------------
def generar_temas(cantidad):
    try:
        prompt = generar_prompt(cantidad)
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un experto en IA que genera temas técnicos innovadores y aplicables a finanzas y economía."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        contenido = response.choices[0].message.content
        temas = [line.strip().strip('"') for line in contenido.split("\n") if line.strip()]
        logger.info(f"Temas generados por IA: {temas}")
        return temas[:cantidad]
    except Exception as e:
        logger.error(f"Error al generar temas: {str(e)}", exc_info=True)
        return []

# ----------------------------
# Leer y guardar JSON
# ----------------------------
def leer_temas_json():
    if TEMAS_JSON_PATH.exists():
        with open(TEMAS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("temas", [])
    return []

def guardar_temas_json(temas):
    with open(TEMAS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"temas": temas}, f, ensure_ascii=False, indent=2)

# ----------------------------
# Ejecución principal
# ----------------------------
if __name__ == "__main__":
    logger.info("==== INICIO GENERACIÓN DE TEMAS ====")

    # Leer temas existentes
    temas_actuales = leer_temas_json()
    logger.info(f"Temas existentes: {len(temas_actuales)}")
    logger.info(f"Lista actual de temas: {temas_actuales}")

    # Calcular cantidad faltante
    cantidad_faltante = NUM_TEMAS_TOTAL - len(temas_actuales)
    if cantidad_faltante <= 0:
        logger.info(f"No se requieren nuevos temas. Ya hay {len(temas_actuales)} disponibles.")
    else:
        logger.info(f"Generando {cantidad_faltante} temas nuevos...")
        nuevos_temas = generar_temas(cantidad_faltante)
        # Evitar duplicados
        nuevos_unicos = [t for t in nuevos_temas if t not in temas_actuales]
        if nuevos_unicos:
            temas_actuales.extend(nuevos_unicos)
            guardar_temas_json(temas_actuales)
            logger.info(f"✅ Se añadieron {len(nuevos_unicos)} nuevos temas.")
            logger.info(f"Lista completa actualizada: {temas_actuales}")
        else:
            logger.info("ℹ️ No se generaron nuevos temas únicos.")

    logger.info("==== FINALIZADO ====")


