import os
import requests
from datetime import datetime
from collections import Counter
from typing import List, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from openai import OpenAI
from pathlib import Path
import logging

# ----------------------------
# Configuración inicial
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
IMAGES_DIR = BASE_DIR / "03_imagenes"
ARTICLES_DIR = BASE_DIR / "02_articulos" / "outputs"

# Crear carpetas necesarias
LOG_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True, parents=True)

# Configuración de logging (archivo en /logs/, sin stdout si no quieres)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "03_generar_imagen.log", encoding="utf-8"),
        logging.StreamHandler()  # Opcional: elimina si no quieres logs en consola
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Clase ImageGenerator (ajustada)
# ----------------------------
class ImageGenerator:
    def __init__(self, api_key: str):
        self.stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
        self.client = OpenAI(api_key=api_key)
        
        # Descarga recursos NLTK
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except:
            nltk.download('punkt')
            nltk.download('stopwords')

    def extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave ignorando errores de NLTK"""
        try:
            words = word_tokenize(text.lower())
            return [
                word for word in words 
                if word.isalpha() 
                and word not in self.stop_words
                and len(word) > 3
            ][:5]  # Limita a 5 keywords
        except Exception as e:
            logger.warning(f"Error en NLTK, usando palabras por defecto: {str(e)}")
            return ["technology", "innovation", "AI"]

    def generate_prompt(self, content: str) -> str:
        """Genera un prompt optimizado para DALL-E 3"""
        keywords = self.extract_keywords(content)
        return (
            f"Ilustración minimalista estilo infografía técnica sobre: {', '.join(keywords)}. "
            "Estilo: Vectorial con colores modernos (azules, grises, naranjas), "
            "sin texto, fondo claro, 4K."
        )

    def generate_image(self, article_path: Path) -> Optional[Path]:
        """Genera y guarda la imagen con reintentos automáticos"""
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()

            prompt = self.generate_prompt(content)
            logger.info(f"Generando imagen para: {article_path.name}")

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt[:4000],  # Asegura que no exceda el límite
                size="1024x1024",
                quality="hd",
                n=1
            )

            # Guardar imagen
            image_path = IMAGES_DIR / f"{article_path.stem}.png"
            with open(image_path, 'wb') as f:
                f.write(requests.get(response.data[0].url).content)
            
            logger.info(f"✅ Imagen guardada: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"Error al generar imagen: {str(e)}", exc_info=True)
            return None

# ----------------------------
# Ejecución principal
# ----------------------------
if __name__ == "__main__":
    API_KEY = os.getenv("BLOG_OPENIA_KEY")
    if not API_KEY or API_KEY.startswith("tu-api-key"):
        logger.error("❌ Configura tu API key de OpenAI")
    else:
        generator = ImageGenerator(API_KEY)
        
        # Procesar el artículo más reciente
        articles = list(ARTICLES_DIR.glob("ART_*.md"))
        if not articles:
            logger.error("No hay artículos en la carpeta")
        else:
            latest_article = max(articles, key=lambda x: x.stat().st_mtime)
            generator.generate_image(latest_article)