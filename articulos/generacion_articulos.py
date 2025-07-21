import os
import random
import requests
import logging
from pathlib import Path
from datetime import datetime

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent  # Raíz del proyecto (auto_blog_ia/)
LOG_DIR = BASE_DIR / "logs"
ARTICULOS_DIR = BASE_DIR / "articulos" / "outputs"
TEMAS_PATH = BASE_DIR / "temas" / "temas.txt"

# Crear carpetas si no existen
ARTICULOS_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "generador_articulos.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de Ollama
API_OLLAMA = "http://localhost:11434/api/generate"
MODELO = "gemma3"  # Ajusta según tu modelo local
TIMEOUT = 300      # 5 minutos

def seleccionar_tema():
    """Selecciona un tema aleatorio del archivo temas.txt."""
    try:
        with open(TEMAS_PATH, "r", encoding="utf-8") as f:
            temas = [line.strip() for line in f.readlines() if line.strip()]
        return random.choice(temas) if temas else None
    except Exception as e:
        logger.error(f"Error al leer temas.txt: {str(e)}", exc_info=True)
        return None

def generar_articulo(tema):
    """Genera un artículo completo basado en un tema."""
    try:
        prompt = f"""
        Escribe un artículo técnico profesional de más de 2000 palabras sobre '{tema}' en español, 
        con un tono equilibrado entre rigor técnico y humor sarcástico inteligente. 
        Sigue esta estructura en formato Markdown:

        Introducción
        Comienza con una anécdota dolorosamente relatable para cualquier profesional del sector, 
        como aquella vez que pasaste tres horas depurando solo para descubrir un error de sintaxis básico. 
        Establece por qué este tema es importante hoy, usando datos contundentes o estadísticas reveladoras. 
        Termina con una promesa clara al lector sobre lo que ganará al terminar de leer.

        Desarrollo
        La teoría que todos creen dominar (pero no)
        Profundiza en el primer concepto fundamental usando analogías 
        mundanas - explica los decoradores en Python como si fueran capas de una cebolla que te hacen llorar. 
        Incluye bloques de código bien comentados con observaciones sarcásticas sobre los errores típicos que todos cometemos.

        Casos de uso en el mundo real
        Presenta ejemplos concretos de empresas que implementaron esta solución, 
        destacando tanto los éxitos como los fracasos épicos. Relátalo como si fuera 
        una historia de supervivencia tecnológica, 
        con lecciones aprendidas y moralejas inesperadas.

        Esas funcionalidades avanzadas que nadie te cuenta
        Explora características menos conocidas pero poderosas, 
        demostrando cómo pueden resolver problemas aparentemente imposibles. 
        Usa comparaciones absurdas pero efectivas para ilustrar su potencial.

        Conclusión
        Resume en una frase contundente el principal aprendizaje. 
        Ofrece recursos genuinamente valiosos para seguir aprendiendo, 
        no simples rellenos. Termina con una llamada a la acción natural pero persuasiva, 
        invitando al lector a aplicar lo aprendido o compartir el artículo con ese 
        compañero que sigue cometiendo los errores que ahora evitará.

        El humor debe surgir de situaciones técnicas reales, no forzado - si el tema es demasiado serio,
        prioriza la claridad sobre el sarcasmo. 
        Los ejemplos de código deben ser relevantes y estar bien comentados, 
        mostrando tanto la forma correcta como los errores comunes con explicaciones de por qué fallan.

        Dame tres titulos sugeridos para dicho articulo...
        """
        
        response = requests.post(
            API_OLLAMA,
            json={
                "model": MODELO,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        logger.error(f"Error al generar artículo: {str(e)}", exc_info=True)
        return None

def guardar_articulo(tema, contenido):
    """Guarda el artículo en la carpeta outputs."""
    try:
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_archivo = ARTICULOS_DIR / f"articulo_{fecha}_{tema[:30]}.md".replace(" ", "_")
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(f"# {tema}\n\n{contenido}")
        return nombre_archivo
    except Exception as e:
        logger.error(f"Error al guardar artículo: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("==== INICIO GENERACIÓN DE ARTÍCULO ====")
    
    # Paso 1: Seleccionar tema
    tema = seleccionar_tema()
    if not tema:
        logger.error("No se encontraron temas en temas.txt")
        exit()

    logger.info(f"Tema seleccionado: {tema}")
    
    # Paso 2: Generar artículo
    articulo = generar_articulo(tema)
    if not articulo:
        logger.error("No se pudo generar el artículo")
        exit()

    # Paso 3: Guardar artículo
    ruta_guardado = guardar_articulo(tema, articulo)
    if ruta_guardado:
        logger.info(f"✅ Artículo guardado en: {ruta_guardado}")
    else:
        logger.error("Error al guardar el artículo")

    logger.info("==== FINALIZADO ====")