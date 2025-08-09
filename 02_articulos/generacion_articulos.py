import os
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
TEMAS_PENDIENTES_PATH = BASE_DIR / "01_temas" / "temas_pendientes.txt"
TEMAS_USADOS_PATH = BASE_DIR / "01_temas" / "temas_usados.txt"

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
    """Toma el primer tema de la cola, lo elimina y lo guarda en el historial."""
    try:
        if not TEMAS_PENDIENTES_PATH.exists():
            logger.error("❌ El archivo de temas pendientes no existe.")
            return None

        with open(TEMAS_PENDIENTES_PATH, "r", encoding="utf-8") as f:
            temas = [line.strip() for line in f if line.strip()]

        if not temas:
            logger.warning("⚠️ No hay temas pendientes disponibles.")
            return None

        tema = temas.pop(0)  # Toma el primer tema de la lista

        # Actualiza el archivo de temas pendientes
        with open(TEMAS_PENDIENTES_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(temas))

        # Registra el tema en el historial
        with open(TEMAS_USADOS_PATH, "a", encoding="utf-8") as f:
            f.write(tema + "\n")

        return tema
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
        Escribe un artículo técnico profesional de más de 2000 palabras sobre '{tema}' en español, 
        con un tono equilibrado entre rigor técnico y humor sarcástico inteligente. 
        Sigue esta estructura en formato Markdown:

        # [Título creativo que combine el tema con una referencia pop]

        ## Introducción
        Comienza con una anécdota relatable. Usa datos contundentes y termina con una promesa al lector.

        ## Desarrollo
        ### Teoría mal entendida
        Profundiza en conceptos fundamentales con analogías y código bien comentado.

        ### Casos reales
        Ejemplos de implementaciones con lecciones aprendidas.

        ### Funcionalidades avanzadas
        Características poco conocidas pero útiles.

        ## Conclusión
        Resumen claro + recursos valiosos + llamada a la acción.

        **Requisitos:**
        - 3 bloques de código con errores/soluciones
        - Emojis moderados en títulos 🚀
        - 80% técnico / 20% humor
        """

        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un ingeniero senior que escribe artículos técnicos con humor inteligente en español."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=4000
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

