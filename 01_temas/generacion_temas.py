import openai
import os
import logging
from pathlib import Path
import sys
import io
from logging.handlers import RotatingFileHandler
from datetime import datetime
from openai import OpenAI
import json
import random

# ----------------------------
# Configuración de OpenAI
# ----------------------------
MODELO = "gpt-4"
OPENAI_API_KEY = os.getenv("BLOG_OPENIA_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
TEMPERATURE = 0.7
MAX_TOKENS = 1000
NUM_TEMAS = 10

# ----------------------------
# Umbral y rutas
# ----------------------------
UMBRAL_TEMAS = 3
RUTA_JSON_TEMAS = Path(__file__).parent / "titulos.json"

# ----------------------------
# Configuración de logging
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            LOG_DIR / "generador_temas.log",
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Prompt de generación ajustado
# ----------------------------
PROMPT = f"""
Genera una lista de {NUM_TEMAS} temas altamente innovadores y orientados al futuro para artículos técnicos sobre:
- Inteligencia Artificial, Machine Learning y Deep Learning aplicados a datos financieros
- Ciencia de Datos avanzada en finanzas, economía y contabilidad
- Modelos predictivos, algoritmos de trading y análisis de riesgos
- Automatización de procesos financieros con IA y sistemas de decisión autónomos
- Data mesh, data fabric y arquitecturas de datos orientadas a empresas y bancos
- IA generativa para optimización financiera, simulaciones económicas y previsiones de mercado
- Integración de IA con Big Data y High Performance Computing en finanzas
- Explainable AI (XAI) para auditoría financiera y cumplimiento regulatorio

Requisitos:
1. Temas concretos, con aplicación práctica o técnica detallada (ej: "Optimización de modelos predictivos para riesgo de crédito usando LLMs").
2. Evitar temas genéricos como 'Qué es Machine Learning' o 'Introducción a la IA'.
3. Evitar temas de salud, medicina o biotecnología.
4. Formato requerido:
   - Un tema por línea
   - Sin numeración
   - Sin caracteres especiales como *, -, etc.
   - Solo el texto del tema
"""

# ----------------------------
# Palabras prohibidas para sesgo
# ----------------------------
PALABRAS_PROHIBIDAS = [
    "qué es", "introducción a", "basics", "fundamentos", "principios"
]

# ----------------------------
# Función para llamar a OpenAI
# ----------------------------
def generar_con_ia(prompt):
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un experto en IA y datos aplicados a finanzas, economía y contabilidad, generando temas técnicos innovadores y bien estructurados."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.9
        )
        logger.info("📥 Respuesta cruda recibida de la API:")
        logger.info(response.choices[0].message.content)
        return response.choices[0].message.content

    except openai.AuthenticationError:
        logger.error("❌ Error de autenticación: Verifica tu API Key.")
    except openai.RateLimitError as e:
        logger.error(f"⏱️ Límite de uso excedido: {str(e)}")
    except Exception as e:
        logger.error("💥 Error inesperado al llamar la API:", exc_info=True)
    return None

# ----------------------------
# Función para procesar respuesta
# ----------------------------
def generar_temas():
    try:
        logger.info(f"🧠 Generando {NUM_TEMAS} temas con el modelo '{MODELO}'...")
        respuesta = generar_con_ia(PROMPT)
        if not respuesta:
            return []

        temas = []
        for t in respuesta.split("\n"):
            t = t.strip()
            if t:
                t = t.split('.', 1)[-1].strip() if t[0].isdigit() else t
                t = t.lstrip('-* ').strip()
                temas.append(t)
        return temas[:NUM_TEMAS]
    except Exception as e:
        logger.error("💥 Error al procesar la respuesta:", exc_info=True)
        return []

# ----------------------------
# Filtrado anti-sesgo y anti-genéricos
# ----------------------------
def filtrar_temas(temas):
    filtrados = []
    for t in temas:
        if len(t.split()) < 5:  # descartar demasiado cortos
            continue
        if any(p.lower() in t.lower() for p in PALABRAS_PROHIBIDAS):
            continue
        filtrados.append(t)
    return filtrados

# ----------------------------
# Guardar JSON
# ----------------------------
def guardar_json(temas):
    data = {
        "temas": temas,
        "generado_en": datetime.utcnow().isoformat()
    }
    with open(RUTA_JSON_TEMAS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"💾 Guardados {len(temas)} temas en {RUTA_JSON_TEMAS}")

# ----------------------------
# Ejecución principal
# ----------------------------
if __name__ == "__main__":
    start_time = datetime.now()
    logger.info("\n" + "="*60)
    logger.info("🚀 INICIO DE EJECUCIÓN")
    logger.info(f"🕒 Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        if not RUTA_JSON_TEMAS.exists():
            temas_actuales = []
        else:
            with open(RUTA_JSON_TEMAS, "r", encoding="utf-8") as f:
                data = json.load(f)
                temas_actuales = data.get("temas", [])

        logger.info(f"📊 Temas pendientes actuales: {len(temas_actuales)}")

        if len(temas_actuales) < UMBRAL_TEMAS:
            temas_nuevos = generar_temas()
            temas_filtrados = filtrar_temas(temas_nuevos)
            if temas_filtrados:
                guardar_json(temas_filtrados)
                estado = "ÉXITO"
            else:
                logger.warning("⚠️ No se generaron temas válidos tras el filtrado.")
                estado = "FALLIDO"
        else:
            logger.info(f"⏸️ No se generaron nuevos temas. Hay suficientes temas pendientes (≥ {UMBRAL_TEMAS}).")
            estado = "SALTEADO"

    except Exception as e:
        logger.critical("🚨 ERROR CRÍTICO DURANTE LA EJECUCIÓN:", exc_info=True)
        estado = "FALLIDO"

    end_time = datetime.now()
    duracion = (end_time - start_time).total_seconds()
    logger.info(f"🕓 Duración total: {duracion:.2f} segundos")
    logger.info(f"🔚 ESTADO FINAL: {estado}")
    logger.info(f"🕒 Fin: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("✅ EJECUCIÓN COMPLETADA")
    logger.info("="*60 + "\n")

