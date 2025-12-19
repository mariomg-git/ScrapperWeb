"""
Administrador centralizado de scrapers
"""
import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)


class ScraperManager:
    """Gestiona los diferentes scrapers disponibles"""
    
    def __init__(self):
        self.scrapers: Dict[str, Dict[str, any]] = {}
    
    def register_scraper(self, key: str, name: str, description: str, execute_func: Callable):
        """
        Registra un nuevo scraper
        
        Args:
            key: Identificador único del scraper
            name: Nombre descriptivo del scraper
            description: Descripción de lo que hace el scraper
            execute_func: Función que ejecuta el scraper
        """
        self.scrapers[key] = {
            'name': name,
            'description': description,
            'execute': execute_func
        }
        logger.info(f"Scraper registrado: {name}")
    
    def list_scrapers(self):
        """Retorna la lista de scrapers disponibles"""
        return self.scrapers
    
    def get_scraper(self, key: str):
        """Obtiene un scraper específico por su clave"""
        return self.scrapers.get(key)
    
    def execute_scraper(self, key: str):
        """Ejecuta un scraper específico"""
        scraper = self.get_scraper(key)
        if scraper:
            logger.info(f"Ejecutando scraper: {scraper['name']}")
            scraper['execute']()
        else:
            logger.error(f"Scraper no encontrado: {key}")
