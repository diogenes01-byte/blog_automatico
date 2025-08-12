import openai
import os
import logging
from pathlib import Path
import sys
import io
from logging.handlers import RotatingFileHandler
from datetime import datetime
from openai import OpenAI

# ----------------------------
# Configuración de OpenAI (CORREGIDO)
# ----------------------------
MODELO = "gpt-4"  # Añade esta línea (o usa "gpt-3.5-turbo" si prefieres)
OPENAI_API_KEY = os.getenv("BLOG_OPENIA_KEY")  # Asegúrate que coincide con tu secret en GitHub
client = OpenAI(api_key=OPENAI_API_KEY)  # Usa la variable correcta
TEMPERATURE = 0.7
MAX_TOKENS = 1000
NUM_TEMAS = 10

# ----------------------------
# Parámetros del sistema de cola
# ----------------------------
UMBRAL_TEMAS = 3  # Si hay menos de este número, se generan más
RUTA_COLA_TEMAS = Path(__file__).parent / "temas_pendientes.txt"

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
# Prompt de generación
# ----------------------------
PROMPT = f"""
Genera una lista de {NUM_TEMAS} temas altamente innovadores y orientados al futuro para artículos técnicos sobre:
- Inteligencia Artificial avanzada y aplicada
- Ciencia de Datos de nueva generación
- Ingeniería de Machine Learning y MLOps a gran escala
- Modelos fundacionales, agentes autónomos y sistemas multiagente
- Data mesh, data fabric y arquitecturas descentralizadas de datos
- Explainable AI (XAI), auditoría algorítmica y confianza en IA
- Edge AI, análisis en tiempo real y procesamiento en el dispositivo
- IA generativa para descubrimientos científicos, simulaciones y diseño de nuevos materiales
- Integración de IA con computación cuántica y HPC (High Performance Computing)
- Automatización cognitiva y toma de decisiones autónoma

Requisitos:
1. Temas concretos, con aplicación práctica o técnica detallada (ej: "Optimización de entrenamiento distribuido de LLMs en clústeres heterogéneos").
2. Evitar temas genéricos como 'Qué es Machine Learning'.
3. Formato requerido:
   - Un tema por línea
   - Sin numeración
   - Sin caracteres especiales como *, -, etc.
   - Solo el texto del tema
"""


# ----------------------------
# Función para llamar a OpenAI
# ----------------------------
def generar_con_ia(prompt):
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un experto en IA que genera temas técnicos innovadores y bien estructurados."},
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
# Manejo de la cola de temas
# ----------------------------
def leer_temas_pendientes():
    if RUTA_COLA_TEMAS.exists():
        with open(RUTA_COLA_TEMAS, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def guardar_temas_pendientes(nuevos_temas):
    existentes = set(leer_temas_pendientes())
    nuevos_unicos = [t for t in nuevos_temas if t not in existentes]
    
    if nuevos_unicos:
        with open(RUTA_COLA_TEMAS, "a", encoding="utf-8") as f:
            for tema in nuevos_unicos:
                f.write(f"{tema}\n")
        logger.info(f"✅ {len(nuevos_unicos)} nuevos temas añadidos a la cola.")
    else:
        logger.info("ℹ️ No hay nuevos temas únicos para añadir.")

# ----------------------------
# Ejecución principal
# ----------------------------
if __name__ == "__main__":
    start_time = datetime.now()
    logger.info("\n" + "="*60)
    logger.info("🚀 INICIO DE EJECUCIÓN")
    logger.info(f"🕒 Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        temas_actuales = leer_temas_pendientes()
        logger.info(f"📊 Temas pendientes actuales: {len(temas_actuales)}")

        if len(temas_actuales) < UMBRAL_TEMAS:
            temas_nuevos = generar_temas()
            if temas_nuevos:
                guardar_temas_pendientes(temas_nuevos)
                estado = "ÉXITO"
            else:
                logger.warning("⚠️ No se generaron temas.")
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
