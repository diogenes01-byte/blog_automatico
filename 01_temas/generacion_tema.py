import os
import json
import yaml
import logging
from datetime import datetime
from openai import OpenAI

# ==========================
# Cargar configuración
# ==========================
with open("01_temas/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

MODEL = config["openai"]["model"]
TEMPERATURE = config["openai"]["temperature"]
MAX_TOKENS = config["openai"]["max_tokens"]

PROMPT = config["prompt"]["template"]

# ==========================
# Configuración de logging
# ==========================
os.makedirs("01_temas/logs", exist_ok=True)
log_filename = datetime.now().strftime("01_temas/logs/%Y%m%d_%H%M%S.log")

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

logging.info("==== Inicio de ejecución de 01_temas ====")

# ==========================
# Inicializar cliente OpenAI
# ==========================
client = OpenAI(api_key=os.getenv("BLOG_OPENIA_KEY"))

# ==========================
# Generar título con reintentos
# ==========================
def generar_tema():
    for intento in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": "Eres un experto en IA aplicada a negocios y finanzas."},
                    {"role": "user", "content": PROMPT},
                ],
            )
            titulo = response.choices[0].message.content.strip()

            if 70 <= len(titulo) <= 120:
                return titulo
            else:
                logging.warning(f"Título inválido en intento {intento+1}: '{titulo}'")
        except Exception as e:
            logging.error(f"Error en intento {intento+1}: {e}")
    return None

tema = generar_tema()

# ==========================
# Guardar resultados
# ==========================
if tema:
    output_json = {
        "timestamp": datetime.now().isoformat(),
        "tema": tema,
        "longitud": len(tema)
    }

    with open("01_temas/tema_actual.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    with open("01_temas/tema.txt", "w", encoding="utf-8") as f:
        f.write(tema + "\n")

    logging.info(f"Tema generado correctamente: {tema}")
else:
    logging.error("No se pudo generar un tema válido después de 3 intentos.")

logging.info("==== Fin de ejecución de 01_temas ====")






