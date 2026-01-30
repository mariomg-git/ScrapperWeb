"""
Scraper de Ejecutivos y Directivos de Empresas en Tijuana
Busca empresas y extrae información de directivos de sus sitios web
"""

import os
import sys
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests
from utils import save_to_json, save_to_csv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tijuana_executives.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TijuanaExecutivesScraper:
    """Scraper especializado en encontrar directivos y ejecutivos de Tijuana"""
    
    def __init__(self, headless: bool = True):
        """
        Inicializa el scraper
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless
        """
        self.headless = headless
        self.driver = None
        self.timeout = 10
        self.executives = []
        self.companies = []
        
        # Palabras clave para identificar secciones de directivos
        self.executive_keywords = [
            'director', 'gerente', 'CEO', 'presidente', 'jefe',
            'ejecutivo', 'administrador', 'líder', 'encargado',
            'manager', 'chief', 'coordinador', 'supervisor'
        ]
        
        # Palabras clave para secciones de equipo/directivos
        self.team_section_keywords = [
            'team', 'equipo', 'leadership', 'directiva', 'directivos',
            'about us', 'nosotros', 'quiénes somos', 'nuestro equipo',
            'executive team', 'management', 'junta directiva'
        ]
    
    def setup_driver(self):
        """Configura el WebDriver de Chrome"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                logger.warning(f"Error con ChromeDriverManager: {e}. Intentando sin service...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.implicitly_wait(self.timeout)
            
            logger.info("WebDriver configurado correctamente")
            return self.driver
            
        except Exception as e:
            logger.error(f"Error al configurar WebDriver: {e}")
            raise
    
    def close_driver(self):
        """Cierra el WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver cerrado")
    
    def search_companies_google(self, query: str, num_results: int = 20) -> List[Dict]:
        """
        Busca empresas en Tijuana usando Google Search
        
        Args:
            query: Término de búsqueda (ej: "empresas Tijuana")
            num_results: Número de resultados deseados
            
        Returns:
            Lista de empresas encontradas
        """
        logger.info(f"Buscando empresas con query: {query}")
        
        search_url = f"https://www.google.com/search?q={query}+Tijuana&num={num_results}"
        companies = []
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            
            # Esperar a que carguen resultados
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "g"))
            )
            
            # Extraer enlaces
            search_results = self.driver.find_elements(By.CLASS_NAME, "g")
            
            for idx, result in enumerate(search_results[:num_results]):
                try:
                    link_elem = result.find_element(By.TAG_NAME, "a")
                    url = link_elem.get_attribute("href")
                    
                    if url and url.startswith("http"):
                        title = result.find_element(By.TAG_NAME, "h3").text
                        
                        companies.append({
                            'name': title,
                            'url': url,
                            'source': 'google_search'
                        })
                        logger.info(f"Empresa encontrada: {title}")
                        
                except Exception as e:
                    logger.debug(f"Error extrayendo resultado {idx}: {e}")
                    continue
            
            self.companies = companies
            logger.info(f"Total de empresas encontradas: {len(companies)}")
            return companies
            
        except Exception as e:
            logger.error(f"Error en búsqueda de Google: {e}")
            return []
    
    def search_companies_local_websites(self) -> List[Dict]:
        """
        Define directamente sitios web populares de empresas en Tijuana
        
        Returns:
            Lista de empresas locales conocidas
        """
        logger.info("Cargando empresas locales conocidas de Tijuana")
        
        # Empresas locales prominentes de Tijuana (ejemplos)
        local_companies = [
            {
                'name': 'Grupo Reforma',
                'url': 'https://www.reforma.com',
                'source': 'local_directory'
            },
            {
                'name': 'Cámara de Comercio Tijuana',
                'url': 'https://www.cctijuana.com',
                'source': 'local_directory'
            },
            {
                'name': 'CONCANACO Tijuana',
                'url': 'https://www.concanaco.com.mx',
                'source': 'local_directory'
            },
            {
                'name': 'Aeropuerto Internacional de Tijuana',
                'url': 'https://www.aeropuertotijuana.com.mx',
                'source': 'local_directory'
            }
        ]
        
        self.companies.extend(local_companies)
        logger.info(f"Empresas locales añadidas: {len(local_companies)}")
        return local_companies
    
    def extract_executives_from_website(self, company: Dict) -> List[Dict]:
        """
        Extrae información de directivos del sitio web de una empresa
        
        Args:
            company: Diccionario con info de empresa
            
        Returns:
            Lista de directivos encontrados
        """
        executives = []
        
        try:
            logger.info(f"Extrayendo ejecutivos de: {company['name']}")
            
            # Intentar descargar con requests primero
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(company['url'], headers=headers, timeout=10)
            response.encoding = 'utf-8'
            html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Buscar secciones de equipo/directivos
            executives.extend(self._search_team_sections(soup, company))
            
            # Búsqueda general por palabras clave
            executives.extend(self._search_by_keywords(soup, company))
            
            logger.info(f"Ejecutivos encontrados en {company['name']}: {len(executives)}")
            return executives
            
        except Exception as e:
            logger.warning(f"Error extrayendo de {company['url']}: {e}")
            return []
    
    def _search_team_sections(self, soup: BeautifulSoup, company: Dict) -> List[Dict]:
        """
        Busca en secciones conocidas de equipo/directivos
        """
        executives = []
        
        try:
            # Buscar por palabras clave en IDs y clases
            for keyword in self.team_section_keywords:
                elements = soup.find_all(['div', 'section'], {
                    'id': re.compile(keyword, re.IGNORECASE),
                    'class': re.compile(keyword, re.IGNORECASE)
                })
                
                for elem in elements:
                    # Buscar nombres y títulos
                    names = self._extract_names_and_titles(elem, company)
                    executives.extend(names)
            
            return executives
            
        except Exception as e:
            logger.debug(f"Error en búsqueda de secciones: {e}")
            return []
    
    def _search_by_keywords(self, soup: BeautifulSoup, company: Dict) -> List[Dict]:
        """
        Busca por palabras clave de ejecutivos en todo el contenido
        """
        executives = []
        
        try:
            # Obtener todo el texto
            text = soup.get_text(separator=' ', strip=True)
            
            # Buscar párrafos que contengan palabras clave
            paragraphs = soup.find_all(['p', 'div', 'li', 'h3', 'h4'])
            
            for para in paragraphs:
                para_text = para.get_text().strip()
                
                # Verificar si contiene palabras de ejecutivo
                if any(keyword.lower() in para_text.lower() for keyword in self.executive_keywords):
                    # Extraer posible nombre (generalmente antes del título)
                    names = self._extract_names_and_titles(para, company)
                    executives.extend(names)
            
            return executives
            
        except Exception as e:
            logger.debug(f"Error en búsqueda por palabras clave: {e}")
            return []
    
    def _extract_names_and_titles(self, element, company: Dict) -> List[Dict]:
        """
        Extrae nombres y títulos de un elemento HTML
        """
        executives = []
        
        try:
            text = element.get_text().strip()
            
            # Patrón: "NOMBRE - TÍTULO" o "NOMBRE\nTÍTULO"
            patterns = [
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*([a-zA-Z\s]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\n([a-zA-Z\s]+)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    name = match.group(1).strip()
                    title = match.group(2).strip()
                    
                    # Validar que no sea demasiado corto
                    if len(name) > 5 and len(title) > 3:
                        executive = {
                            'name': name,
                            'title': title,
                            'company': company['name'],
                            'company_url': company['url'],
                            'source': 'website_scrape',
                            'extracted_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Evitar duplicados
                        if executive not in executives:
                            executives.append(executive)
            
            return executives
            
        except Exception as e:
            logger.debug(f"Error extrayendo nombres: {e}")
            return []
    
    def run_scraper(self, search_query: str = "empresas directorio Tijuana", 
                   use_local_companies: bool = True, 
                   num_google_results: int = 10):
        """
        Ejecuta el scraper completo
        
        Args:
            search_query: Término de búsqueda en Google
            use_local_companies: Si incluir empresas locales conocidas
            num_google_results: Número de resultados de Google
        """
        try:
            self.setup_driver()
            
            logger.info("="*60)
            logger.info("INICIANDO SCRAPER DE EJECUTIVOS TIJUANA")
            logger.info("="*60)
            
            # Cargar empresas locales conocidas
            if use_local_companies:
                self.search_companies_local_websites()
            
            # Buscar en Google (opcional)
            if search_query:
                self.search_companies_google(search_query, num_google_results)
            
            logger.info(f"\nTotal de empresas a procesar: {len(self.companies)}")
            
            # Extraer ejecutivos de cada empresa
            for idx, company in enumerate(self.companies, 1):
                logger.info(f"\n[{idx}/{len(self.companies)}] Procesando: {company['name']}")
                
                executives = self.extract_executives_from_website(company)
                self.executives.extend(executives)
                
                # Pausa para no sobrecargar
                time.sleep(2)
            
            # Guardar resultados
            self._save_results()
            
            logger.info("\n" + "="*60)
            logger.info(f"SCRAPER COMPLETADO - Total ejecutivos encontrados: {len(self.executives)}")
            logger.info("="*60)
            
            return self.executives
            
        except Exception as e:
            logger.error(f"Error en scraper: {e}")
            return []
        
        finally:
            self.close_driver()
    
    def _save_results(self):
        """Guarda los resultados en JSON y CSV"""
        if not self.executives:
            logger.warning("No se encontraron ejecutivos para guardar")
            return
        
        try:
            # Crear carpeta con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_folder = os.path.join("data", f"executives_tijuana_{timestamp}")
            os.makedirs(output_folder, exist_ok=True)
            
            # Guardar JSON
            json_filename = f"executives_tijuana_{timestamp}.json"
            json_filepath = os.path.join(output_folder, json_filename)
            save_to_json(self.executives, json_filepath)
            
            # Guardar CSV
            csv_filename = f"executives_tijuana_{timestamp}.csv"
            csv_filepath = os.path.join(output_folder, csv_filename)
            save_to_csv(self.executives, csv_filepath)
            
            logger.info(f"Resultados guardados en: {output_folder}")
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")


def main():
    """Función principal"""
    
    scraper = TijuanaExecutivesScraper(headless=True)
    
    # Configuración personalizable
    executives = scraper.run_scraper(
        search_query="empresas Tijuana",
        use_local_companies=True,
        num_google_results=10
    )
    
    # Mostrar resultados
    if executives:
        print("\n" + "="*60)
        print("EJECUTIVOS ENCONTRADOS:")
        print("="*60)
        
        for exec in executives[:10]:  # Mostrar los primeros 10
            print(f"\nNombre: {exec.get('name', 'N/A')}")
            print(f"   Cargo: {exec.get('title', 'N/A')}")
            print(f"   Empresa: {exec.get('company', 'N/A')}")
        
        if len(executives) > 10:
            print(f"\n... y {len(executives) - 10} más")


if __name__ == "__main__":
    main()
