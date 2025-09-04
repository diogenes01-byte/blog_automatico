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
# Prompt
# ----------------------------------------------------
PROMPT_TEMPLATE = """
Redacta un artículo técnico y narrativo en español, de entre 1500 y 2000 palabras,
a partir del siguiente título:

"{titulo}"

Requisitos:
1) Enfócate en Inteligencia Artificial, Machine Learning, Deep Learning, Ingeniería de datos
   y su aplicación concreta a finanzas, contabilidad, economía o mercados.
2) Incluye explicaciones técnicas y ejemplos prácticos, pero con claridad para público experto.
3) Evita frases genéricas, salud/medicina y auto-referencias ("en este artículo hablaremos…").
4) Usa subtítulos, párrafos bien estructurados y tono profesional.
5) No incluyas conclusiones triviales; aporta ideas de arquitectura, tendencias y retos futuros.
""".strip()


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



