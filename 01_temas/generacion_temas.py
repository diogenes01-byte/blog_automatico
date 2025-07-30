import openai
import os
import logging
from pathlib import Path
import sys
import io
from logging.handlers import RotatingFileHandler
from openai import OpenAI

# ----------------------------
# Configuración de OpenAI (GPT-4.5 Preview)
# ----------------------------
OPENAI_API_KEY = ""
MODELO = "gpt-4.5-preview"  # Modelo avanzado
TEMPERATURE = 0.7
MAX_TOKENS = 1000  # Aumentado para mejor calidad
NUM_TEMAS = 10

# Inicializar cliente
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Configuración inicial
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
# Función optimizada para GPT-4.5
# ----------------------------
def generar_con_ia(prompt):
    """Genera texto usando GPT-4.5 Preview con manejo de errores mejorado"""
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en IA que genera temas técnicos innovadores y bien estructurados."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.9  # Parámetro adicional para mejor calidad
        )
        return response.choices[0].message.content
    
    except openai.AuthenticationError as e:
        logger.error(f"Error de autenticación: Verifica tu API Key")
        return None
    except openai.RateLimitError as e:
        logger.error(f"Límite de tasa excedido: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return None

# ----------------------------
# Prompt mejorado para GPT-4.5
# ----------------------------
PROMPT = f"""
Genera exactamente {NUM_TEMAS} temas avanzados sobre IA con este formato:

**Título del Tema**  
[Área principal] | [Nivel de dificultad]  
Descripción concisa (máximo 15 palabras)  

Ejemplo:  
**Optimización de Transformers para Edge Computing**  
[ML Engineering] | [Avanzado]  
Técnicas para desplegar modelos grandes en dispositivos IoT  

Requisitos:
- Enfoque en aplicaciones prácticas (no teóricas)
- Máximo 1 línea por componente (título, área, descripción)
- {NUM_TEMAS} temas exactamente
- Incluye al menos 3 temas sobre LLMs y 2 sobre Edge AI
"""

# ----------------------------
# Función principal mejorada
# ----------------------------
def generar_temas():
    try:
        logger.info(f"Generando {NUM_TEMAS} temas avanzados con {MODELO}...")
        respuesta = generar_con_ia(PROMPT)
        if not respuesta:
            return []
            
        # Procesamiento mejorado
        temas = [t.strip() for t in respuesta.split("\n\n") if t.strip() and "**" in t]
        return temas[:NUM_TEMAS]
    
    except Exception as e:
        logger.error(f"Error al procesar respuesta: {str(e)}", exc_info=True)
        return []

if __name__ == "__main__":
    try:
        logger.info("==== INICIO ====")
        temas = generar_temas()
        
        if temas:
            temas_path = BASE_DIR / "temas" / "temas.txt"
            temas_path.parent.mkdir(exist_ok=True)
            
            with open(temas_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(temas))  # Doble salto de línea entre temas
            logger.info(f"✅ {len(temas)} temas avanzados guardados en {temas_path}")
        else:
            logger.error("⚠️ No se generaron temas. Verifica los logs.")
            
        logger.info("==== FINALIZADO ====")
    except Exception as e:
        logger.critical(f"🚨 ERROR CRÍTICO: {str(e)}", exc_info=True)