# 01_temas/generacion_temas.py

import os
import re
import json
import sys
import io
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from openai import OpenAI

# ----------------------------
# Configuración general
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

RUTA_TEMA_ACTUAL = Path(__file__).parent / "tema_actual.json"

# Modelo y API
MODELO = "gpt-4o"  # Consistente con la carpeta 02
OPENAI_API_KEY = os.getenv("BLOG_OPENIA_KEY")
TEMPERATURE = 0.8
MAX_TOKENS = 350

# ----------------------------
# Logging (UTF-8 + rotación)
# ----------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(
    RotatingFileHandler(
        LOG_DIR / "generador_tema_actual.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
)
logger.addHandler(logging.StreamHandler())

# ----------------------------
# Cliente OpenAI
# ----------------------------
if not OPENAI_API_KEY:
    logger.critical("❌ Falta la variable de entorno BLOG_OPENIA_KEY.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Prompt (un solo título)
# ----------------------------
PROMPT = """
Genera exactamente 1 título (una sola línea) para un artículo técnico en español que combine:
- Inteligencia Artificial / Machine Learning / Deep Learning / Ingeniería de datos
- Con aplicaciones concretas a finanzas, economía, contabilidad, mercados o riesgo

Requisitos estrictos:
1) Título específico y orientado a práctica o arquitectura técnica (no generalidades).
2) Evita por completo temas de salud, medicina o biomedicina.
3) Prohibidas las frases o variantes: "Qué es", "Introducción a", "Guía básica", "Fundamentos de", "Historia de",
   "Beneficios de", "Ventajas de", "Desventajas de", "Panorama general", "Conceptos básicos".
4) Sin numeraciones, sin viñetas, sin comillas, sin emojis, una sola línea.
5) Longitud orientativa: 70-120 caracteres.

Ejemplos de estilo (NO los repitas):
- Optimización de carteras con aprendizaje por refuerzo y restricciones de riesgo no lineales
- Detección de anomalías en pagos instantáneos con autoencoders y grafos transaccionales
- Evaluación contrafactual de estrategias algorítmicas con modelos causales estructurales

Devuelve solo el título, nada más.
""".strip()


def limpiar_titulo(texto: str) -> str:
    """Quita comillas, numeraciones/viñetas y espacios redundantes."""
    if texto is None:
        return ""
    t = texto.strip()

    # Si viene con múltiples líneas, quedarse con la primera no vacía
    if "\n" in t:
        for line in t.splitlines():
            line = line.strip()
            if line:
                t = line
                break

    # Quitar comillas de borde
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("“") and t.endswith("”")):
        t = t[1:-1].strip()

    # Quitar viñetas o numeración al inicio: "1. ", "1) ", "- ", "* ", "• "
    t = re.sub(r'^\s*(?:\d+[\.\)]\s+|[-*•]\s+)', '', t)

    # Colapsar espacios
    t = re.sub(r'\s+', ' ', t).strip()

    # Asegurar que no termina en comillas sueltas
    t = t.strip('"“”').strip()
    return t


def generar_titulo() -> str:
    """Llama a OpenAI para generar un único título y lo limpia."""
    try:
        logger.info("🧠 Solicitando 1 título al modelo...")
        resp = client.chat.completions.create(
            model=MODELO,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un arquitecto de datos y ML con foco en finanzas y economía. "
                        "Propones títulos técnicos, específicos y aplicados."
                    ),
                },
                {"role": "user", "content": PROMPT},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        crudo = resp.choices[0].message.content or ""
        logger.info(f"📥 Respuesta cruda: {crudo!r}")
        limpio = limpiar_titulo(crudo)
        logger.info(f"🧹 Título limpio: {limpio!r}")
        return limpio
    except Exception:
        logger.exception("💥 Error al generar el título con OpenAI")
        return ""


def guardar_tema_actual(titulo: str) -> None:
    data = {
        "tema": titulo,
        "generado_en": datetime.utcnow().isoformat() + "Z",
    }
    with open(RUTA_TEMA_ACTUAL, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"💾 Tema guardado en {RUTA_TEMA_ACTUAL}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 INICIO GENERACIÓN DE TEMA ÚNICO")

    titulo = generar_titulo()
    if not titulo:
        logger.error("❌ No se obtuvo un título válido; abortando.")
        sys.exit(1)

    guardar_tema_actual(titulo)
    logger.info(f"✅ Título final: {titulo}")
    logger.info("🏁 FINALIZADO")
    logger.info("=" * 60)




