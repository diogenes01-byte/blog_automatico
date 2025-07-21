import requests
import os
import logging
from pathlib import Path
import subprocess
import time
import sys
import io
from logging.handlers import RotatingFileHandler

# Configuración para soporte UTF-8 en consola
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ----------------------------
# Configuración inicial
# ----------------------------
BASE_DIR = Path(__file__).parent.parent  # Apunta a auto_blog_ia/
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configuración mejorada de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            LOG_DIR / "generador_temas.log",
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Configuración de Ollama (sin cambios)
# ----------------------------
API_OLLAMA = "http://localhost:11434/api/generate"
MODELO = "gemma3"
TIMEOUT = 180
NUM_TEMAS = 10

# ----------------------------
# Funciones auxiliares (sin cambios)
# ----------------------------
def verificar_ollama():
    """Verifica si el servidor Ollama está activo."""
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Debug: Error al verificar Ollama - {str(e)}")
        return False

def iniciar_ollama():
    """Intenta iniciar Ollama si no está corriendo."""
    try:
        subprocess.Popen(["ollama", "serve"], shell=True)
        time.sleep(5)
        logger.debug("Debug: Ollama iniciado")
    except Exception as e:
        logger.error(f"No se pudo iniciar Ollama: {str(e)}")

def generar_temas():
    """Genera temas usando Ollama con manejo robusto de errores."""
    try:
        if not verificar_ollama():
            logger.warning("Ollama no está activo. Intentando iniciar...")
            iniciar_ollama()
            time.sleep(10)

        logger.info(f"Generando {NUM_TEMAS} temas con {MODELO}...")
        response = requests.post(
            API_OLLAMA,
            json={
                "model": MODELO,
                "prompt": PROMPT,
                "stream": False,
                "options": {"temperature": 0.8}
            },
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        temas = [t.strip() for t in response.json()["response"].split("\n") if t.strip()]
        logger.info(f"✅ {len(temas)} temas generados")
        return temas

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión: {str(e)}")
        logger.error("Soluciones posibles:")
        logger.error("1. Ejecuta 'ollama serve' en otra terminal")
        logger.error(f"2. Verifica que el modelo '{MODELO}' esté descargado (ollama pull {MODELO})")
        return []
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return []

# ----------------------------
# Prompt (sin cambios)
# ----------------------------
PROMPT = f"""
Genera una lista de {NUM_TEMAS} temas innovadores para artículos técnicos sobre:
- Inteligencia Artificial
- Ciencia de Datos
- Ingeniería de ML
- Modelos fundacionales y agentes autónomos
- Data mesh y data fabric
- Explainable AI (XAI) y modelos interpretables
- Edge AI y análisis en tiempo real
- IA generativa para ciencia y descubrimientos

Requisitos:
1. Temas específicos (ej: "Cómo optimizar Pandas para datasets de 10GB").
2. Evitar temas genéricos como 'Qué es Machine Learning'.
3. Formato: 1 tema por línea, sin numeración ni comillas.
"""

if __name__ == "__main__":
    try:
        logger.info("==== INICIO ====")
        
        temas = generar_temas()
        if temas:
            # Ruta ajustada para auto_blog_ia/temas/temas.txt
            temas_path = BASE_DIR / "temas" / "temas.txt"
            temas_path.parent.mkdir(exist_ok=True)  # Crea la carpeta si no existe
            
            with open(temas_path, "w", encoding="utf-8") as f:
                f.write("\n".join(temas))
            logger.info(f"📄 Temas guardados en {temas_path}")
        else:
            logger.warning("No se generaron temas. Verifica logs anteriores.")

        logger.info("==== FINALIZADO ====")
    except Exception as e:
        logger.critical(f"ERROR CRÍTICO: {str(e)}", exc_info=True)