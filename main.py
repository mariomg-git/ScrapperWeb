"""
Script principal de ejemplo para web scraping
"""
import time
import logging
from selenium.webdriver.common.by import By
from scraper import WebScraper
from utils import save_to_json, save_to_csv, log_scraping_stats, clean_text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def scrape_example_site():
    """
    Ejemplo de scraping de un sitio web
    Modifica esta función según tus necesidades
    """
    # URL a scrapear
    url = "https://quotes.toscrape.com/"
    
    # Lista para almacenar datos
    scraped_data = []
    start_time = time.time()
    
    # Usar context manager para manejar automáticamente el driver
    with WebScraper(headless=False) as scraper:
        # Navegar a la página
        if not scraper.get_page(url):
            logger.error("No se pudo cargar la página")
            return
        
        # Esperar a que carguen las citas
        scraper.wait_for_element(By.CLASS_NAME, "quote")
        
        # Encontrar todos los elementos de citas
        quotes = scraper.find_elements_safe(By.CLASS_NAME, "quote")
        logger.info(f"Se encontraron {len(quotes)} citas")
        
        # Extraer datos de cada cita
        for idx, quote in enumerate(quotes, 1):
            try:
                # Extraer texto
                text_element = quote.find_element(By.CLASS_NAME, "text")
                text = clean_text(text_element.text)
                
                # Extraer autor
                author_element = quote.find_element(By.CLASS_NAME, "author")
                author = clean_text(author_element.text)
                
                # Extraer tags
                tag_elements = quote.find_elements(By.CLASS_NAME, "tag")
                tags = [clean_text(tag.text) for tag in tag_elements]
                
                # Crear diccionario con datos
                data = {
                    "id": idx,
                    "text": text,
                    "author": author,
                    "tags": tags,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                scraped_data.append(data)
                logger.info(f"Cita {idx} extraída: {author}")
                
            except Exception as e:
                logger.error(f"Error extrayendo cita {idx}: {e}")
                continue
        
        # Tomar screenshot
        scraper.take_screenshot("example_screenshot.png")
    
    # Calcular duración
    duration = time.time() - start_time
    
    # Mostrar estadísticas
    log_scraping_stats(
        total_items=len(quotes),
        success=len(scraped_data),
        failed=len(quotes) - len(scraped_data),
        duration=duration
    )
    
    # Guardar datos
    if scraped_data:
        save_to_json(scraped_data, "quotes.json")
        save_to_csv(scraped_data, "quotes.csv")
        logger.info(f"Se extrajeron {len(scraped_data)} citas exitosamente")
    else:
        logger.warning("No se extrajeron datos")


def scrape_custom_site(url: str):
    """
    Función plantilla para scrapear un sitio personalizado
    
    Args:
        url: URL del sitio a scrapear
    """
    scraped_data = []
    
    with WebScraper(headless=True) as scraper:
        if not scraper.get_page(url):
            return
        
        # TODO: Implementar lógica de scraping específica
        # Ejemplo:
        # scraper.wait_for_element(By.CSS_SELECTOR, "tu-selector")
        # elements = scraper.find_elements_safe(By.CSS_SELECTOR, "tu-selector")
        
        # for element in elements:
        #     data = {
        #         "field1": element.find_element(...).text,
        #         "field2": element.find_element(...).text,
        #     }
        #     scraped_data.append(data)
        
        pass
    
    # Guardar datos
    if scraped_data:
        save_to_json(scraped_data)
        save_to_csv(scraped_data)


if __name__ == "__main__":
    logger.info("Iniciando web scraper...")
    
    # Ejecutar ejemplo
    scrape_example_site()
    
    # Para scrapear un sitio personalizado:
    # scrape_custom_site("https://tu-sitio.com")
    
    logger.info("Scraping completado")
