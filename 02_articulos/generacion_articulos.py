import os
import logging
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import json
import random

# ----------------------------
# Configuración de rutas
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
ARTICULOS_DIR = BASE_DIR / "02_articulos" / "outputs"
TITULOS_JSON_PATH = BASE_DIR / "01_temas" / "titulos.json"

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
TEMPERATURE = 0.8

# ----------------------------
# Selección y manejo del tema
# ----------------------------
def seleccionar_tema():
    """Selecciona un tema al azar del JSON y actualiza la lista."""
    try:
        if not TITULOS_JSON_PATH.exists():
            logger.error("❌ El archivo titulos.json no existe.")
            return None

        with open(TITULOS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            temas = data.get("temas", [])

        if not temas:
            logger.warning("⚠️ No hay temas pendientes disponibles.")
            return None

        # Elegir un tema al azar
        tema = random.choice(temas)
        temas.remove(tema)

        # Guardar JSON actualizado
        data["temas"] = temas
        with open(TITULOS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return tema
    except Exception as e:
        logger.error(f"Error al procesar titulos.json: {str(e)}", exc_info=True)
        return None

# ----------------------------
# Generación del artículo
# ----------------------------
def generar_articulo(tema):
    """Genera un artículo técnico completo a partir de un tema."""
    try:
        prompt = f"""
ROL
Eres un redactor profesional experto en Inteligencia Artificial, Machine Learning y Deep Learning aplicados a finanzas, economía y contabilidad. Combina rigor técnico con narrativa atractiva y humor sutil.

TAREA
Escribe un artículo técnico en español de entre 1500 y 2000 palabras sobre: "{tema}". Mantén narrativa continua, transiciones naturales y cambios de tono para separar secciones implícitas. Evita títulos o subtítulos explícitos.

CONTEXTO
Público profesional y curioso, que busca profundidad técnica y aplicaciones prácticas en el mundo financiero y de datos.

REQUISITOS
- Abrir con anécdota o situación relatable ligada a finanzas o economía.
- Explicar conceptos clave con analogías, ejemplos reales y casos financieros.
- Incluir predicciones y tendencias a 2-5 años sobre la temática.
- Incorporar citas breves de papers, expertos o fuentes reconocidas.
- Cierre con resumen claro, recursos útiles y llamada a la acción.
- Mantener entre 80% contenido técnico y 20% humor ligero.
- No usar fragmentos de código.
- Párrafos cortos y lectura fluida.
- Introducir frases puente o micro-resúmenes para evitar bloques largos.
- Usar emojis con moderación (máximo uno por transición).
- No temas genéricos, salud o medicina.

CONDICIONES
- No entregar menos de 1500 palabras.
- Mantener tono atractivo y coherente durante todo el artículo.
"""

        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un ingeniero senior que escribe artículos técnicos con humor inteligente y aplicaciones en finanzas, economía y datos."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=7500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error al generar artículo: {str(e)}", exc_info=True)
        return None

# ----------------------------
# Guardado del artículo
# ----------------------------
def guardar_articulo(tema, contenido):
    """Guarda el artículo como archivo Markdown con nombre basado en el tema."""
    try:
        fecha = datetime.now().strftime("%d-%m-%y")
        palabras_clave = [
            p for p in tema.lower().split()
            if p not in ["de", "para", "en", "y", "con", "como", "con"]
            and len(p) > 3 and p.isalpha()
        ][:3]

        palabras_str = "_".join(palabras_clave)
        nombre_archivo = ARTICULOS_DIR / f"ART_{fecha}_{palabras_str}.md"

        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(contenido)

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
        exit()

    logger.info(f"📌 Tema seleccionado: {tema}")

    articulo = generar_articulo(tema)
    if not articulo:
        logger.error("❌ Falló la generación del artículo.")
        exit()

    ruta_guardado = guardar_articulo(tema, articulo)
    if ruta_guardado:
        logger.info(f"✅ Artículo guardado en: {ruta_guardado}")
        logger.info(f"📝 Longitud aproximada: {len(articulo.split())} palabras.")
    else:
        logger.error("❌ Error al guardar el artículo.")

    logger.info("==== FINALIZADO ====")


