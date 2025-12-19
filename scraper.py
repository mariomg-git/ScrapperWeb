"""
Clase base para web scraping con Selenium
"""
import os
import time
import logging
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class WebScraper:
    """Clase base para realizar web scraping con Selenium"""
    
    def __init__(self, headless: bool = True, timeout: int = 3):
        """
        Inicializa el scraper
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless
            timeout: Tiempo máximo de espera para elementos (segundos)
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def setup_driver(self):
        """Configura y retorna el WebDriver de Chrome"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
            
            # Configuraciones adicionales para mejorar rendimiento
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Inicializar driver con manejo de errores mejorado
            try:
                # Intentar con ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                logger.warning(f"Error con ChromeDriverManager: {e}. Intentando sin service...")
                # Intentar sin especificar service (usar chromedriver del PATH)
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.implicitly_wait(self.timeout)
            
            logger.info("WebDriver configurado correctamente")
            return self.driver
            
        except Exception as e:
            logger.error(f"Error al configurar WebDriver: {e}")
            raise
    
    def get_page(self, url: str) -> bool:
        """
        Navega a una URL
        
        Args:
            url: URL a visitar
            
        Returns:
            True si la navegación fue exitosa, False en caso contrario
        """
        try:
            logger.info(f"Navegando a: {url}")
            self.driver.get(url)
            time.sleep(2)  # Espera básica para carga inicial
            return True
        except Exception as e:
            logger.error(f"Error al navegar a {url}: {e}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[object]:
        """
        Espera a que un elemento esté presente
        
        Args:
            by: Tipo de selector (By.ID, By.CLASS_NAME, etc.)
            value: Valor del selector
            timeout: Tiempo máximo de espera (usa self.timeout por defecto)
            
        Returns:
            Elemento encontrado o None
        """
        try:
            wait_time = timeout or self.timeout
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"Timeout esperando elemento: {value}")
            return None
    
    def find_elements_safe(self, by: By, value: str) -> List:
        """
        Busca elementos de forma segura
        
        Args:
            by: Tipo de selector
            value: Valor del selector
            
        Returns:
            Lista de elementos encontrados (vacía si no hay)
        """
        try:
            elements = self.driver.find_elements(by, value)
            return elements
        except NoSuchElementException:
            logger.warning(f"No se encontraron elementos: {value}")
            return []
    
    def scroll_to_bottom(self, pause_time: float = 1.5):
        """
        Hace scroll hasta el final de la página
        
        Args:
            pause_time: Tiempo de pausa entre scrolls
        """
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll hacia abajo
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            
            # Calcular nueva altura
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
                
            last_height = new_height
    
    def take_screenshot(self, filename: str = "screenshot.png"):
        """
        Toma una captura de pantalla
        
        Args:
            filename: Nombre del archivo
        """
        try:
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot guardado: {filepath}")
        except Exception as e:
            logger.error(f"Error al tomar screenshot: {e}")
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver cerrado")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
