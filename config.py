"""
Archivo de configuración del proyecto
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración general del scraper"""
    
    # Configuración del navegador
    HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
    BROWSER = os.getenv("BROWSER", "chrome")
    TIMEOUT = int(os.getenv("TIMEOUT", "10"))
    
    # URLs
    TARGET_URL = os.getenv("TARGET_URL", "https://example.com")
    
    # Directorios
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")
    LOG_DIR = "logs"
    
    # Gmail configuration
    GMAIL_USER = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    
    # Delays (en segundos)
    MIN_DELAY = 1
    MAX_DELAY = 3
    SCROLL_PAUSE = 1.5
    
    # User Agents
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    # Configuración de logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configuración específica de scrapers
    SCRAPERS = {
        'offerup': {
            'name': 'OfferUp Scraper',
            'description': 'Busca productos en OfferUp',
            'default_headless': False
        },
        'clothing': {
            'name': 'Clothing Image Scraper',
            'description': 'Descarga imágenes de ropa de sitios web',
            'default_headless': False,
            'max_images': 20
        }
    }
    
    @classmethod
    def create_directories(cls):
        """Crea los directorios necesarios"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)
