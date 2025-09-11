# 02_articulos/generacion_articulos.py

import os
import sys
import io
import json
import re
import random
import logging
import yaml
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from openai import OpenAI

# ----------------------------
# Configuración
# ----------------------------
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OPENAI_API_KEY = os.getenv("BLOG_OPENIA_KEY")
if not OPENAI_API_KEY:
    print("❌ Falta la variable de entorno BLOG_OPENIA_KEY.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Logging
# ----------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

log_dir = Path(config["paths"]["log_dir"])
log_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(
    RotatingFileHandler(
        log_dir / config["paths"]["log_file"],
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
)
logger.addHandler(logging.StreamHandler())

# ----------------------------
# Rutas y archivos
# ----------------------------
RUTA_TEMA_ACTUAL = Path(config["paths"]["tema_actual"])
RUTA_SALIDA = Path(config["paths"]["salida"])
HISTORIAL_PATH = BASE_DIR / "historial.json"

# ----------------------------
# Funciones auxiliares
# ----------------------------
def limpiar_titulo(t: str) -> str:
    if not t:
        return ""
    t = t.strip()
    if "\n" in t:
        t = t.splitlines()[0].strip()
    t = re.sub(r'^\s*(?:\d+[\.\)]\s+|[-*•]\s+)', '', t)
    t = t.strip('"“”')
    return t.strip()

def cargar_titulo() -> str:
    if not RUTA_TEMA_ACTUAL.exists():
        logger.error(f"❌ No se encontró {RUTA_TEMA_ACTUAL}")
        return ""
    try:
        with open(RUTA_TEMA_ACTUAL, "r", encoding="utf-8") as f:
            data = json.load(f)
        return limpiar_titulo(data.get("tema", ""))
    except Exception:
        logger.exception("💥 Error al leer el tema actual.")
        return ""

def seleccionar_estilo() -> str:
    estilos = config.get("narrativas", [])
    usados = []
    if HISTORIAL_PATH.exists():
        try:
            with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
                usados = json.load(f)
        except Exception:
            logger.warning("⚠️ No se pudo leer historial.json, se reiniciará.")
            usados = []

    disponibles = [e for e in estilos if e not in usados]
    if not disponibles:
        usados = []
        disponibles = estilos.copy()

    estilo = random.choice(disponibles)
    usados.append(estilo)

    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(usados, f, ensure_ascii=False, indent=2)

    logger.info(f"🎨 Estilo elegido: {estilo}")
    return estilo

def generar_articulo(titulo: str, estilo: str) -> str:
    prompt = config["prompt"].format(titulo=titulo, estilo=estilo)
    try:
        resp = client.chat.completions.create(
            model=config["openai"]["model"],
            messages=[
                {"role": "system", "content": "Eres un experto en IA aplicada a finanzas y negocios."},
                {"role": "user", "content": prompt},
            ],
            temperature=config["openai"]["temperature"],
            max_tokens=config["openai"]["max_tokens"],
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

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 INICIO GENERACIÓN DE ARTÍCULO")

    titulo = cargar_titulo()
    if not titulo:
        logger.error("🚫 No se pudo cargar un título válido. Abortando.")
        sys.exit(1)

    estilo = seleccionar_estilo()
    articulo = generar_articulo(titulo, estilo)
    if not articulo:
        logger.error("🚫 El modelo no devolvió contenido. Abortando.")
        sys.exit(1)

    guardar_articulo(titulo, articulo)
    logger.info(f"✅ Artículo generado para: {titulo}")
    logger.info("🏁 FINALIZADO")
    logger.info("=" * 60)




