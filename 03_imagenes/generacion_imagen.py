import os
import requests
from datetime import datetime
from collections import Counter
from typing import List, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from openai import OpenAI  # Nueva sintaxis para openai>=1.0.0

API_KEY = os.getenv("DALLE_KEY_IMAGE")

# Configuración inicial de NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')

class ImageGenerator:
    def __init__(self, api_key: str):
        """
        Inicializa el generador de imágenes.
        
        Args:
            api_key (str): API Key de OpenAI (https://platform.openai.com/api-keys)
        """
        self.stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
        self.client = OpenAI(api_key=api_key)  # Cliente nuevo para OpenAI>=1.0.0
        
        # Configuración de carpetas (rutas absolutas)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.dirs = {
            'articles': os.path.join(self.base_dir, 'articulos', 'outputs'),
            'images': os.path.join(self.base_dir, 'imagenes'),
            'logs': os.path.join(self.base_dir, 'logs')
        }
        
        self._create_dirs()
    
    def _create_dirs(self):
        """Crea las carpetas necesarias (sin subcarpetas no deseadas)"""
        try:
            os.makedirs(self.dirs['images'], exist_ok=True)
            os.makedirs(self.dirs['logs'], exist_ok=True)
            self._log("Directorios verificados")
        except Exception as e:
            self._log(f"Error creando directorios: {str(e)}", "ERROR")
            raise
    
    def _log(self, message: str, level: str = "INFO"):
        """Registra eventos en el archivo de log"""
        log_file = os.path.join(self.dirs['logs'], 'image_generator.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    
    def extract_keywords(self, text: str, num_keywords: int = 5) -> List[str]:
        """Extrae palabras clave del texto (con manejo de errores para NLTK)"""
        try:
            # Verifica recursos de NLTK
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalpha() and word not in self.stop_words]
            word_freq = Counter(words)
            return [word for word, _ in word_freq.most_common(num_keywords)]
            
        except Exception as e:
            self._log(f"Error extrayendo keywords: {str(e)}", "ERROR")
            return []
    
    def generate_prompt(self, keywords: List[str], article_title: str = "") -> str:
        """Genera un prompt optimizado para DALL-E"""
        try:
            base = "Digital art, 4K, high detail, trending on ArtStation, featuring: "
            elements = f"Main elements: {', '.join(keywords)}. Style: vibrant colors, professional composition."
            
            return f"{base}'{article_title}'. {elements}" if article_title else f"{base}{elements}"
        except Exception as e:
            self._log(f"Error generando prompt: {str(e)}", "ERROR")
            return ""
    
    def generate_image(self, content: str, title: str = "", filename: str = None) -> Optional[str]:
        """Genera una imagen con DALL-E 3 (OpenAI 1.0.0+)"""
        try:
            keywords = self.extract_keywords(content)
            if not keywords:
                raise ValueError("No se extrajeron palabras clave")
                
            prompt = self.generate_prompt(keywords, title)
            if not prompt:
                raise ValueError("No se pudo generar el prompt")
            
            # Llamada a la API de OpenAI (versión 1.0.0+)
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard"
            )
            
            # Descargar y guardar imagen
            img_name = filename or f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img_path = os.path.join(self.dirs['images'], img_name)
            
            img_data = requests.get(response.data[0].url).content
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            self._log(f"Imagen generada: {img_path}")
            return img_path
            
        except Exception as e:
            self._log(f"Error generando imagen: {str(e)}", "ERROR")
            return None
    
    def process_markdown_file(self, md_file: str):
        """Procesa un archivo .md y genera su imagen"""
        try:
            if not md_file.endswith('.md'):
                return None
                
            file_path = os.path.join(self.dirs['articles'], md_file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Saltar metadata (opcional)
            if content.startswith('---'):
                content = content.split('---', 2)[2].strip()
            
            title = content.split('\n')[0].strip()
            img_filename = f"{os.path.splitext(md_file)[0]}_image.png"
            
            return self.generate_image(content, title, img_filename)
            
        except Exception as e:
            self._log(f"Error procesando {md_file}: {str(e)}", "ERROR")
            return None

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    # >>> REEMPLAZA CON TU API KEY REAL <<<
    API_KEY = API_KEY
    
    if not API_KEY or API_KEY.startswith("sk-tu-api-key"):
        print("ERROR: Configura tu API key de OpenAI en la variable 'API_KEY'")
    else:
        generator = ImageGenerator(API_KEY)
        
        # Procesar todos los archivos .md en articles/outputs
        processed_files = 0
        for file in os.listdir(generator.dirs['articles']):
            if file.endswith('.md'):
                result = generator.process_markdown_file(file)
                if result:
                    print(f"✅ Imagen generada para {file}: {result}")
                    processed_files += 1
                    
        print(f"\n✔ Proceso completado. Imágenes generadas: {processed_files}")
        print(f"📁 Carpeta de imágenes: {generator.dirs['images']}")