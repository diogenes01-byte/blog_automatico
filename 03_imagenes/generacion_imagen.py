import os
import requests
from datetime import datetime
from collections import Counter
from typing import List, Optional
import random
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from openai import OpenAI
from pathlib import Path
import logging
import re
import numpy as np

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

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "03_generar_imagen.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Clase ImageGenerator (optimizada con embeddings)
# ----------------------------
class ImageGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
        
        # Descargar recursos NLTK si no están
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except:
            nltk.download('punkt')
            nltk.download('stopwords')

    def extract_keywords_semantic(self, text: str, resumen: str) -> List[str]:
        """Extrae keywords usando embeddings y relevancia semántica"""
        try:
            # Tokenización básica
            palabras = re.findall(r'\b[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}\b', text.lower())
            stopwords_basicas = {
                "esta", "este", "para", "como", "donde", "cuando", "todo",
                "pero", "porque", "datos", "tecnologia", "tecnológico",
                "machine", "learning", "inteligencia", "artificial", "sistema"
            }
            candidatos = list(set(p for p in palabras if p not in stopwords_basicas))

            # Embedding del resumen
            resumen_vec = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=resumen
            ).data[0].embedding

            # Calcular similitud coseno para cada candidato
            resultados = []
            for palabra in candidatos:
                vec = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=palabra
                ).data[0].embedding
                sim = np.dot(resumen_vec, vec) / (np.linalg.norm(resumen_vec) * np.linalg.norm(vec))
                resultados.append((palabra, sim))

            resultados.sort(key=lambda x: x[1], reverse=True)
            return [palabra for palabra, _ in resultados[:5]]

        except Exception as e:
            logger.warning(f"Fallo en extracción semántica: {str(e)}")
            return None

    def extract_keywords_fallback(self, text: str) -> List[str]:
        """Método de respaldo usando NLTK y frecuencia"""
        try:
            words = [
                w for w in word_tokenize(text.lower())
                if w.isalpha()
                and w not in self.stop_words
                and len(w) > 3
            ]
            palabras_genericas = {
                "datos", "data", "información", "sistema", "tecnología",
                "machine", "learning", "inteligencia", "artificial"
            }
            words = [w for w in words if w not in palabras_genericas]

            counter = Counter(words)
            mas_comunes = [palabra for palabra, _ in counter.most_common(15)]
            seleccion = random.sample(mas_comunes, min(5, len(mas_comunes)))
            return seleccion

        except Exception as e:
            logger.warning(f"Error en fallback NLTK: {str(e)}")
            return ["technology", "innovation", "AI"]

    def extract_keywords(self, text: str, resumen: str) -> List[str]:
        """Híbrido: primero semántica, luego fallback"""
        keywords_sem = self.extract_keywords_semantic(text, resumen)
        if keywords_sem and len(keywords_sem) >= 3:
            return keywords_sem
        return self.extract_keywords_fallback(text)

    def generate_prompt(self, content: str) -> str:
        """Genera un prompt optimizado y coherente con el artículo para DALL·E 3"""
        resumen = ' '.join(content.strip().split()[:50])
        keywords = self.extract_keywords(content, resumen)

        estilos = [
            "ilustración digital futurista",
            "render hiperrealista con iluminación dramática",
            "minimalista estilo infografía técnica",
            "concept art cinematográfico",
            "estilo isométrico 3D con sombras suaves"
        ]
        estilo_elegido = random.choice(estilos)

        return (
            f"{estilo_elegido} que represente visualmente el tema del artículo: "
            f"'{resumen}'. Incluir elementos como {', '.join(keywords)} "
            "con un ambiente tecnológico y profesional, paleta de colores fríos (azules, violetas, grises), "
            "sin texto, formato horizontal, estética limpia y en alta resolución."
        )

    def generate_image(self, article_path: Path) -> Optional[Path]:
        """Genera y guarda la imagen con reintentos automáticos"""
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()

            prompt = self.generate_prompt(content)
            logger.info(f"Generando imagen para: {article_path.name}")
            logger.info(f"Prompt usado: {prompt}")

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt[:4000],
                size="1024x1024",
                quality="hd",
                n=1
            )

            # ⇩⇩⇩ AJUSTE ÚNICO: guardar con el mismo nombre del artículo + .png
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
        articles = list(ARTICLES_DIR.glob("ART_*.md"))
        if not articles:
            logger.error("No hay artículos en la carpeta")
        else:
            latest_article = max(articles, key=lambda x: x.stat().st_mtime)
            generator.generate_image(latest_article)



