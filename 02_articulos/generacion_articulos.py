import os
import json
import logging
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# ----------------------------
# Configuración de rutas
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
ARTICULOS_DIR = BASE_DIR / "02_articulos" / "outputs"
TEMAS_JSON_PATH = BASE_DIR / "01_temas" / "temas_pendientes.json"
TEMAS_USADOS_PATH = BASE_DIR / "01_temas" / "temas_usados.json"

ARTICULOS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ----------------------------
# Configuración de logging
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
# Selección y manejo del tema
# ----------------------------
def seleccionar_tema():
    """Toma el primer tema del JSON, lo elimina y lo guarda en historial."""
    if not TEMAS_JSON_PATH.exists():
        logger.error("❌ El archivo de temas pendientes no existe.")
        return None

    try:
        with open(TEMAS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Acepta tanto lista como diccionario con clave "temas"
        if isinstance(data, list):
            temas = [t for t in data if isinstance(t, str) and t.strip()]
        elif isinstance(data, dict) and "temas" in data:
            temas = [t for t in data.get("temas", []) if isinstance(t, str) and t.strip()]
        else:
            logger.error(f"Formato de JSON inesperado en {TEMAS_JSON_PATH}")
            return None

        if not temas:
            logger.warning("⚠️ No hay temas pendientes disponibles.")
            return None

        tema = temas.pop(0)
        logger.info(f"📌 Tema seleccionado: {tema}")

        # Reescribe el JSON con los temas restantes
        with open(TEMAS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(temas, f, ensure_ascii=False, indent=2)

        # Registra en historial
        historial = []
        if TEMAS_USADOS_PATH.exists():
            try:
                with open(TEMAS_USADOS_PATH, "r", encoding="utf-8") as fu:
                    historial = json.load(fu) if isinstance(json.load(fu), list) else []
            except Exception:
                historial = []

        historial.append({"tema": tema, "fecha": datetime.now().isoformat()})
        with open(TEMAS_USADOS_PATH, "w", encoding="utf-8") as fu:
            json.dump(historial, fu, ensure_ascii=False, indent=2)

        return tema

    except json.JSONDecodeError:
        logger.error("❌ Error de parseo JSON en el archivo de temas.", exc_info=True)
    except Exception as e:
        logger.error(f"Error al procesar la cola de temas: {str(e)}", exc_info=True)
    return None

# ----------------------------
# Generación del artículo
# ----------------------------
def generar_articulo(tema):
    """Genera un artículo técnico completo a partir de un tema."""
    try:
        prompt = f"""
Actúa como redactor técnico profesional especializado en IA, ciencia de datos y finanzas.
Redacta un artículo narrativo y profundo de entre 1500 y 2000 palabras (mínimo 1500) en español,
sobre el siguiente tema: {tema}.

Instrucciones:
- Tono profesional con 80% contenido técnico y 20% humor inteligente.
- No usar títulos explícitos, el texto debe fluir con transiciones naturales.
- Abrir con anécdota o dato impactante, incluir explicaciones técnicas con analogías,
  referencias breves a estudios o expertos, casos de uso, y predicciones a 2-5 años.
- Concluir con un resumen y una llamada a la acción.
- Párrafos cortos y fáciles de leer, sin fragmentos de código, máximo un emoji por transición.
"""

        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un ingeniero senior que escribe artículos técnicos de IA y finanzas en español con humor sutil."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=6000
        )
        texto = response.choices[0].message.content.strip()
        # Elimina comillas innecesarias si el modelo devuelve el título entrecomillado
        if texto.startswith('"') and texto.endswith('"'):
            texto = texto[1:-1].strip()
        return texto
    except Exception as e:
        logger.error(f"Error al generar artículo: {str(e)}", exc_info=True)
        return None

# ----------------------------
# Guardado del artículo
# ----------------------------
def guardar_articulo(tema, contenido):
    """Guarda el artículo como Markdown."""
    try:
        fecha = datetime.now().strftime("%d-%m-%y")
        palabras_clave = [
            p for p in tema.lower().split()
            if p not in ["de", "para", "en", "y", "con", "como", "con"]
            and len(p) > 3 and p.isalpha()
        ][:3]
        palabras_str = "_".join(palabras_clave) or "articulo"
        nombre_archivo = ARTICULOS_DIR / f"ART_{fecha}_{palabras_str}.md"

        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(contenido)

        logger.info(f"✅ Artículo guardado en: {nombre_archivo}")
        logger.info(f"📝 Longitud aproximada: {len(contenido.split())} palabras.")
        return nombre_archivo
    except Exception as e:
        logger.error(f"Error al guardar artículo: {str(e)}", exc_info=True)
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



