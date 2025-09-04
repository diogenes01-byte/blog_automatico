# 02_articulos/generacion_articulos.py

import os
import sys
import io
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from openai import OpenAI

# ----------------------------------------------------
# Configuración de rutas
# ----------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

RUTA_TEMA_ACTUAL = BASE_DIR / "01_temas" / "tema_actual.json"
RUTA_SALIDA = Path(__file__).parent / "articulo_generado.json"

# Parámetros del modelo
MODELO = "gpt-4o"
TEMPERATURE = 0.8
MAX_TOKENS = 7500  # nos da espacio para ~1500-2000 palabras
OPENAI_API_KEY = os.getenv("BLOG_OPENIA_KEY")

# ----------------------------------------------------
# Logging
# ----------------------------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(
    RotatingFileHandler(
        LOG_DIR / "generador_articulos.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
)
logger.addHandler(logging.StreamHandler())

# ----------------------------------------------------
# Cliente OpenAI
# ----------------------------------------------------
if not OPENAI_API_KEY:
    logger.critical("❌ Falta la variable de entorno BLOG_OPENIA_KEY.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------------------------------
# Prompt como plantilla limpia
# ----------------------------------------------------
PROMPT_TEMPLATE = """
ROL: Actúa como redactor técnico profesional especializado en divulgación tecnológica y científica enfocado a finanzas y negocios, 
con habilidad para combinar rigor técnico y humor inteligente, manteniendo al lector enganchado de principio a fin.

TAREA: Escribe un artículo técnico en español de entre 1200 y 1500 palabras sobre {titulo} 
con narrativa continua, sin títulos o subtítulos explícitos, y con transiciones naturales y cambios de tono 
para separar secciones implícitas.

CONTEXTO: El artículo está destinado a un público profesional y curioso, que busca profundidad técnica 
pero disfruta de un toque de ironía o sarcasmo inteligente. El contenido debe poder usarse como cuerpo 
principal de un correo o como entrada de blog.

RAZONAMIENTO:
  - Abrir con una anécdota o situación relatable, datos contundentes y una promesa clara de valor al lector.
  - Explicar los conceptos clave con analogías creativas, referencias culturales o históricas, y ejemplos reales.
  - Incluir casos prácticos y aprendizajes derivados de ellos.
  - Incorporar citas breves de expertos, papers o fuentes reconocidas.
  - Explorar funcionalidades avanzadas o perspectivas futuras sobre el tema.
  - Cerrar con un resumen claro, recursos útiles y una llamada a la acción convincente.
  - Mantener un poco de humor en el texto
  - Usar emojis con moderación uno o dos maximos.

SALIDA: Generar un artículo narrativo que incluya:
  - Historia inicial que conecte emocionalmente.
  - Explicaciones técnicas profundas con analogías.
  - Casos de uso reales y aprendizajes.
  - Predicciones y tendencias a 2-5 años.
  - Inclusión de citas para respaldar afirmaciones clave.
  - Conclusión con recursos y llamada a la acción.

CONDICIONES:
  - No entregues un artículo MENOR de 1200 palabras.
  - Sin fragmentos de código.
  - Párrafos cortos y de lectura fluida.
  - Usar un tono atractivo desde la primera línea.
  - Incluir variaciones de tono para mantener el ritmo narrativo.
  - Introducir frases-puente o micro-resúmenes intermedios.
  - No abusar de tecnicismos sin explicación.
""".strip()

# ----------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------
def limpiar_titulo(t: str) -> str:
    """Elimina comillas, viñetas y espacios redundantes del título."""
    if not t:
        return ""
    t = t.strip()
    if "\n" in t:
        t = t.splitlines()[0].strip()
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("“") and t.endswith("”")):
        t = t[1:-1].strip()
    t = re.sub(r'^\s*(?:\d+[\.\)]\s+|[-*•]\s+)', '', t)
    return t.strip('"“”').strip()


def cargar_titulo() -> str:
    """Lee el título de 01_temas/tema_actual.json."""
    if not RUTA_TEMA_ACTUAL.exists():
        logger.error(f"❌ No se encontró {RUTA_TEMA_ACTUAL}")
        return ""
    try:
        with open(RUTA_TEMA_ACTUAL, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return limpiar_titulo(data.get("tema", ""))
        logger.error("⚠️ El JSON de tema_actual no es un dict válido.")
        return ""
    except Exception:
        logger.exception("💥 Error al leer el tema actual.")
        return ""


def generar_articulo(titulo: str) -> str:
    """Llama a OpenAI y genera el cuerpo del artículo."""
    try:
        logger.info(f"🧠 Generando artículo para: {titulo!r}")
        resp = client.chat.completions.create(
            model=MODELO,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en IA aplicada a finanzas, negocios y datos. "
                        "Creas contenido técnico, profundo y bien estructurado."
                    ),
                },
                {"role": "user", "content": PROMPT_TEMPLATE.format(titulo=titulo)},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return resp.choices[0].message.content or ""
    except Exception:
        logger.exception("💥 Error al generar el artículo con OpenAI")
        return ""


def guardar_articulo(titulo: str, contenido: str):
    data = {
        "titulo": titulo,
        "cuerpo": contenido,
        "generado_en": datetime.utcnow().isoformat() + "Z",
    }
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"💾 Artículo guardado en {RUTA_SALIDA}")


# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 INICIO GENERACIÓN DE ARTÍCULO")

    titulo = cargar_titulo()
    if not titulo:
        logger.error("🚫 No se pudo cargar un título válido. Abortando.")
        sys.exit(1)

    articulo = generar_articulo(titulo)
    if not articulo:
        logger.error("🚫 El modelo no devolvió contenido. Abortando.")
        sys.exit(1)

    guardar_articulo(titulo, articulo)
    logger.info(f"✅ Artículo generado para: {titulo}")
    logger.info("🏁 FINALIZADO")
    logger.info("=" * 60)



