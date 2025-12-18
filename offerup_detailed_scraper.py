"""
Scraper detallado de OfferUp - Entra a cada producto individual
"""
import re
import time
import logging
import os
import signal
import sys
import smtplib
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from time import perf_counter
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scraper import WebScraper
from utils import save_to_json, save_to_csv, clean_text
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('offerup_detailed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Diccionario para tracking de tiempos
timing_stats = {}

# Variable global para manejar interrupción
interrupted = False

def signal_handler(sig, frame):
    """Manejador para Ctrl+C - guarda datos antes de salir"""
    global interrupted
    interrupted = True
    logger.warning("\n\n⚠️  Interrupción detectada (Ctrl+C)")
    logger.info("Finalizando de forma segura y guardando datos recolectados...")

def log_timing(step_name, start_time):
    """Helper para logear tiempo de ejecución de cada paso"""
    elapsed = time.perf_counter() - start_time
    timing_stats[step_name] = elapsed
    logger.info(f"⏱️  {step_name}: {elapsed:.2f}s")
    return elapsed

def print_timing_summary():
    """Imprime un resumen organizado de todos los tiempos"""
    logger.info("\n" + "="*70)
    logger.info("📊 RESUMEN DETALLADO DE TIEMPOS POR OPERACIÓN")
    logger.info("="*70)
    
    # Agrupar por categorías
    categories = {
        "Setup Inicial": [],
        "Configuración": [],
        "Búsqueda y Filtros": [],
        "Obtención de Enlaces": [],
        "Extracción de Productos": [],
        "Navegación de Páginas": [],
        "Total": []
    }
    
    for key, value in sorted(timing_stats.items(), key=lambda x: x[1], reverse=True):
        if "Navegación inicial" in key:
            categories["Setup Inicial"].append((key, value))
        elif "Configuración de ubicación" in key:
            categories["Configuración"].append((key, value))
        elif "Búsqueda" in key or "filtros" in key:
            categories["Búsqueda y Filtros"].append((key, value))
        elif "enlaces" in key:
            categories["Obtención de Enlaces"].append((key, value))
        elif "Producto" in key or "└─" in key:
            categories["Extracción de Productos"].append((key, value))
        elif "Página" in key:
            categories["Navegación de Páginas"].append((key, value))
        elif "TOTAL" in key:
            categories["Total"].append((key, value))
    
    for category, items in categories.items():
        if items:
            logger.info(f"\n📂 {category}:")
            for name, duration in sorted(items, key=lambda x: x[1], reverse=True):
                logger.info(f"  {name}: {duration:.2f}s")
    
    logger.info("\n" + "="*70 + "\n")


class OfferUpDetailedScraper:
    """Scraper que entra a cada producto de OfferUp"""
    
    def __init__(self, headless=False):
        self.scraper = WebScraper(headless=headless, timeout=15)
        self.base_url = "https://offerup.com/"
        self.all_products = []
    
    def configure_location(self, zip_code: str = "92101"):
        """
        Configura la ubicación en OfferUp usando código postal (basado en recorded_actions.json)
        
        Args:
            zip_code: Código postal (ej: "92101" para San Diego)
        """
        logger.info(f"Configurando ubicación con código postal: {zip_code}")
        try:
            time.sleep(3)
            
            # PASO 1: Click en el elemento de ubicación actual (Santa Monica:, etc)
            # Buscar SPAN con clase MuiTypography-subtitle1 que contenga ":"
            location_spans = self.scraper.driver.find_elements(By.XPATH, 
                "//span[contains(@class, 'MuiTypography-subtitle1') and contains(text(), ':')]")
            
            clicked_location = False
            for elem in location_spans:
                try:
                    if elem.is_displayed():
                        logger.info(f"Ubicación actual detectada: {elem.text}")
                        self.scraper.driver.execute_script("arguments[0].click();", elem)
                        time.sleep(3)
                        clicked_location = True
                        logger.info("✓ PASO 1: Clic en ubicación actual")
                        break
                except:
                    continue
            
            if not clicked_location:
                logger.warning("No se pudo hacer clic en la ubicación, intentando alternativa...")
                return False
            
            # PASO 2: Click en la ubicación mostrada en el modal (Santa Monica, CA 90403)
            time.sleep(2)
            current_location_p = self.scraper.driver.find_elements(By.XPATH, 
                "//p[contains(@class, 'MuiTypography-body1')]")
            
            clicked_current = False
            for elem in current_location_p:
                try:
                    text = elem.text
                    if elem.is_displayed() and ('CA' in text or len(text) > 10):
                        logger.info(f"Haciendo clic en: {text}")
                        self.scraper.driver.execute_script("arguments[0].click();", elem)
                        time.sleep(3)
                        clicked_current = True
                        logger.info("✓ PASO 2: Clic en ubicación actual en modal")
                        break
                except:
                    continue
            
            # PASO 3: Buscar y hacer clic en el campo INPUT para código postal
            time.sleep(2)
            all_inputs = self.scraper.driver.find_elements(By.TAG_NAME, "input")
            zip_input = None
            
            for inp in all_inputs:
                try:
                    if inp.is_displayed():
                        # Buscar input con clase MuiInputBase-input jss232 jss1102
                        classes = inp.get_attribute('class') or ''
                        if 'MuiInputBase-input' in classes and inp.get_attribute('type') != 'search':
                            zip_input = inp
                            logger.info(f"✓ PASO 3: Campo de código postal encontrado")
                            break
                except:
                    continue
            
            if zip_input:
                # PASO 3: Click en el campo
                zip_input.click()
                time.sleep(1)
                
                # Borrar TODO el contenido del input (CTRL+A y DELETE)
                zip_input.send_keys(Keys.CONTROL + "a")
                time.sleep(0.3)
                zip_input.send_keys(Keys.DELETE)
                time.sleep(0.3)
                
                # Asegurar que está vacío usando JavaScript también
                self.scraper.driver.execute_script("arguments[0].value = '';", zip_input)
                time.sleep(0.5)
                logger.info("✓ Campo de código postal limpiado")
                
                # PASO 4: Escribir código postal carácter por carácter
                for char in zip_code:
                    zip_input.send_keys(char)
                    time.sleep(0.15)
                
                logger.info(f"✓ PASO 4: Código postal escrito: {zip_input.get_attribute('value')}")
                time.sleep(2)
                
                # PASO 5: Click en botón "Apply"
                apply_buttons = self.scraper.driver.find_elements(By.XPATH, 
                    "//span[contains(@class, 'MuiTypography') and text()='Apply']")
                
                for btn in apply_buttons:
                    try:
                        if btn.is_displayed():
                            self.scraper.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(3)
                            logger.info("✓ PASO 5: Clic en Apply")
                            break
                    except:
                        continue
                
                # PASO 6: Click en "See listings"
                time.sleep(2)
                see_listings_buttons = self.scraper.driver.find_elements(By.XPATH, 
                    "//span[contains(@class, 'MuiTypography') and text()='See listings']")
                
                for btn in see_listings_buttons:
                    try:
                        if btn.is_displayed():
                            self.scraper.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(3)
                            logger.info("✓ PASO 6: Clic en See listings")
                            logger.info(f"✓✓✓ Ubicación configurada exitosamente: {zip_code}")
                            return True
                    except:
                        continue
                        
            logger.warning("No se pudo completar la configuración de ubicación")
            return False
                
        except Exception as e:
            logger.error(f"Error configurando ubicación: {e}")
            return False
    
    def apply_price_filters(self, min_price: int, max_price: int):
        """
        Aplica filtros de precio
        
        Args:
            min_price: Precio mínimo
            max_price: Precio máximo
        """
        logger.info(f"Aplicando filtros de precio: ${min_price} - ${max_price}")
        try:
            time.sleep(3)
            
            # Scroll hacia arriba para asegurar que los filtros están visibles
            self.scraper.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Buscar TODOS los inputs en la página
            all_inputs = self.scraper.driver.find_elements(By.TAG_NAME, "input")
            
            # Filtrar solo los que son de tipo text y están visibles
            text_inputs = []
            for inp in all_inputs:
                try:
                    if inp.is_displayed() and inp.get_attribute('type') in ['text', 'number', None]:
                        # Verificar si es un campo de precio (suelen tener $ o números)
                        placeholder = inp.get_attribute('placeholder') or ''
                        aria_label = inp.get_attribute('aria-label') or ''
                        if '$' in placeholder or 'price' in placeholder.lower() or 'price' in aria_label.lower():
                            text_inputs.append(inp)
                        elif len(text_inputs) < 2 and inp.size['height'] > 0:  # Campo visible
                            text_inputs.append(inp)
                except:
                    continue
            
            logger.info(f"Encontrados {len(text_inputs)} campos de texto visibles")
            
            if len(text_inputs) >= 2:
                try:
                    # Hacer scroll al elemento para asegurarse que está visible
                    self.scraper.driver.execute_script("arguments[0].scrollIntoView(true);", text_inputs[0])
                    time.sleep(0.5)
                    
                    # Precio mínimo - usar JavaScript para mayor confiabilidad
                    logger.info(f"Escribiendo precio mínimo: {min_price}")
                    text_inputs[0].click()
                    time.sleep(0.5)
                    text_inputs[0].clear()
                    time.sleep(0.3)
                    # Escribir carácter por carácter con delay
                    for char in str(min_price):
                        text_inputs[0].send_keys(char)
                        time.sleep(0.1)
                    logger.info(f"✓ Precio mínimo: ${min_price}")
                    time.sleep(1)
                    
                    # Precio máximo - escribir MUY despacio
                    self.scraper.driver.execute_script("arguments[0].scrollIntoView(true);", text_inputs[1])
                    time.sleep(0.5)
                    logger.info(f"Escribiendo precio máximo: {max_price}")
                    text_inputs[1].click()
                    time.sleep(0.5)
                    text_inputs[1].clear()
                    time.sleep(0.3)
                    # Escribir carácter por carácter con delay mayor
                    for char in str(max_price):
                        text_inputs[1].send_keys(char)
                        time.sleep(0.15)  # Delay más largo entre caracteres
                    
                    # Verificar que se escribió correctamente
                    actual_value = text_inputs[1].get_attribute('value')
                    logger.info(f"Valor escrito en campo máximo: '{actual_value}'")
                    
                    # Si no se escribió completo, intentar con JavaScript
                    if actual_value != str(max_price):
                        logger.warning(f"Valor incorrecto, reintentando con JavaScript...")
                        self.scraper.driver.execute_script(f"arguments[0].value = '{max_price}';", text_inputs[1])
                        time.sleep(0.3)
                        actual_value = text_inputs[1].get_attribute('value')
                        logger.info(f"Nuevo valor: '{actual_value}'")
                    
                    logger.info(f"✓ Precio máximo: ${max_price}")
                    time.sleep(1.5)
                    
                    # Buscar botón Go usando múltiples estrategias
                    go_found = False
                    
                    # Estrategia 1: XPath con texto
                    try:
                        go_btn = self.scraper.driver.find_element(By.XPATH, "//button[contains(., 'Go')]")
                        if go_btn.is_displayed():
                            self.scraper.driver.execute_script("arguments[0].click();", go_btn)
                            logger.info("✓ Filtros aplicados (botón Go - XPath)")
                            go_found = True
                            time.sleep(4)
                    except:
                        pass
                    
                    # Estrategia 2: Buscar todos los botones y verificar texto
                    if not go_found:
                        try:
                            all_buttons = self.scraper.driver.find_elements(By.TAG_NAME, "button")
                            for btn in all_buttons:
                                if btn.text.strip().lower() == 'go' and btn.is_displayed():
                                    self.scraper.driver.execute_script("arguments[0].click();", btn)
                                    logger.info("✓ Filtros aplicados (botón Go - JavaScript)")
                                    go_found = True
                                    time.sleep(4)
                                    break
                        except:
                            pass
                    
                    # Estrategia 3: Presionar Enter si no se encontró el botón
                    if not go_found:
                        text_inputs[1].send_keys(Keys.RETURN)
                        logger.info("✓ Filtros aplicados (Enter)")
                        time.sleep(4)
                        
                except Exception as e:
                    logger.error(f"Error interactuando con campos: {e}")
            else:
                logger.warning(f"Solo se encontraron {len(text_inputs)} campos, se necesitan al menos 2")
                
        except Exception as e:
            logger.error(f"Error aplicando filtros: {e}")
    
    def get_product_links(self, max_items=20):
        """
        Obtiene los enlaces de productos de la página actual
        
        Args:
            max_items: Máximo de items a obtener
            
        Returns:
            Lista de URLs de productos
        """
        logger.info("Obteniendo enlaces de productos...")
        product_links = []
        
        try:
            time.sleep(1.5)  # Reducido de 3s a 1.5s
            
            # Scroll para cargar más items
            for _ in range(2):
                self.scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Reducido de 2s a 1s
            
            # Buscar enlaces a productos
            link_selectors = [
                "a[href*='/item/']",
                "a[href*='/detail/']"
            ]
            
            links = []
            for selector in link_selectors:
                links = self.scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    logger.info(f"Encontrados {len(links)} enlaces con selector: {selector}")
                    break
            
            # Extraer URLs únicas
            seen_urls = set()
            for link in links:
                try:
                    url = link.get_attribute('href')
                    if url and '/item/' in url and url not in seen_urls:
                        product_links.append(url)
                        seen_urls.add(url)
                        if len(product_links) >= max_items:
                            break
                except:
                    continue
            
            logger.info(f"✓ Se obtuvieron {len(product_links)} enlaces únicos")
            
        except Exception as e:
            logger.error(f"Error obteniendo enlaces: {e}")
        
        return product_links[:max_items]
    
    def extract_product_details(self, product_url: str, index: int):
        """
        Entra a un producto individual y extrae toda la información
        
        Args:
            product_url: URL del producto
            index: Índice del producto
            
        Returns:
            Diccionario con datos del producto
        """
        logger.info(f"\n[{index}] Entrando a producto: {product_url}")
        
        product_data = {
            "index": index,
            "url": product_url,
            "title": "",
            "price": "",
            "price_value": None,
            "description": "",
            "condition": "",
            "location": "",
            "seller_name": "",
            "posted_date": "",
            "images": [],
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Navegar al producto
            nav_start = time.perf_counter()
            self.scraper.driver.get(product_url)
            time.sleep(2)
            log_timing(f"      └─ Navegación a producto", nav_start)
            
            # Obtener todo el texto de la página para extraer información
            text_start = time.perf_counter()
            page_text = self.scraper.driver.find_element(By.TAG_NAME, "body").text
            log_timing(f"      └─ Obtención de texto de página", text_start)
            
            # Título - Usar el título de la página como fallback
            title_start = time.perf_counter()
            try:
                page_title = self.scraper.driver.title
                if page_title and page_title != "OfferUp":
                    product_data["title"] = clean_text(page_title.split('-')[0].strip())
                    logger.info(f"  Título: {product_data['title'][:50]}...")
            except:
                pass
            
            # Buscar título en la página
            title_selectors = ["h1", "h2", "[data-testid='item-title']"]
            for selector in title_selectors:
                try:
                    title_elem = self.scraper.driver.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text and len(title_elem.text) > 3:
                        product_data["title"] = clean_text(title_elem.text)
                        logger.info(f"  Título: {product_data['title'][:50]}...")
                        break
                except:
                    continue
            log_timing(f"      └─ Extracción de título", title_start)
            
            # Precio - buscar en el texto de la página
            price_start = time.perf_counter()
            price_pattern = r'\$[\d,]+(?:\.\d{2})?'
            prices_found = re.findall(price_pattern, page_text)
            if prices_found:
                product_data["price"] = prices_found[0]  # Tomar el primer precio encontrado
                try:
                    price_match = re.search(r'[\d,]+', product_data["price"].replace('$', ''))
                    if price_match:
                        product_data["price_value"] = int(price_match.group().replace(',', ''))
                    logger.info(f"  Precio: {product_data['price']}")
                except:
                    pass
            log_timing(f"      └─ Extracción de precio", price_start)
            
            # Descripción - buscar en múltiples lugares con timeout corto
            desc_start = time.perf_counter()
            desc_selectors = [
                "[data-testid='item-description']",
                "div[class*='description']",
                "p[class*='description']",
                "pre"
            ]
            # Reducir temporalmente el implicit wait para descripción
            original_timeout = self.scraper.driver.timeouts.implicit_wait
            self.scraper.driver.implicitly_wait(1)  # Solo 1 segundo para descripción
            
            for selector in desc_selectors:
                try:
                    desc_elem = self.scraper.driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem and desc_elem.text and len(desc_elem.text) > 20:
                        product_data["description"] = clean_text(desc_elem.text)[:500]
                        logger.info(f"  Descripción: {len(product_data['description'])} caracteres")
                        break
                except:
                    continue
            
            # Restaurar timeout original
            self.scraper.driver.implicitly_wait(original_timeout)
            log_timing(f"      └─ Extracción de descripción", desc_start)
            
            # Extraer ubicación del texto
            location_start = time.perf_counter()
            if "San Diego" in page_text or "CA" in page_text:
                # Buscar patrón de ubicación
                location_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})', page_text)
                if location_match:
                    product_data["location"] = location_match.group(1)
            log_timing(f"      └─ Extracción de ubicación", location_start)
            
            # Imágenes - extracción inmediata sin delay
            try:
                img_start = time.perf_counter()
                img_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, "img")
                for img in img_elements[:5]:
                    src = img.get_attribute('src')
                    if src and ('offerup' in src or 'cloudfront' in src) and src.startswith('http'):
                        product_data["images"].append(src)
                if product_data["images"]:
                    logger.info(f"  Imágenes: {len(product_data['images'])} encontradas")
                log_timing(f"      └─ Extracción de imágenes", img_start)
            except:
                pass
            
            logger.info(f"✓ Producto {index} extraído exitosamente")
            
        except Exception as e:
            logger.error(f"Error extrayendo producto {index}: {e}")
        
        return product_data
    
    def scrape_with_pagination(self, search_term: str, location: str, min_price: int, max_price: int, 
                                max_items: int = 100):
        """
        Scraping completo con paginación dinámica
        
        Args:
            search_term: Término de búsqueda
            location: Ubicación
            min_price: Precio mínimo
            max_price: Precio máximo
            max_items: Total de items a extraer (default: 100)
        """
        logger.info("\n" + "="*60)
        logger.info("INICIANDO SCRAPING DETALLADO DE OFFERUP")
        logger.info("="*60)
        logger.info(f"Búsqueda: {search_term}")
        logger.info(f"Ubicación: {location}")
        logger.info(f"Precio: ${min_price} - ${max_price}")
        logger.info(f"Total de items a extraer: {max_items}")
        logger.info("="*60 + "\n")
        
        scraping_start = time.perf_counter()
        
        try:
            self.scraper.setup_driver()
            
            # 1. Navegar a OfferUp
            step_start = time.perf_counter()
            logger.info("Paso 1: Navegando a OfferUp...")
            self.scraper.get_page(self.base_url)
            logger.info("⏳ Esperando 20 segundos para que cargue completamente...")
            time.sleep(20)
            log_timing("1. Navegación inicial + carga", step_start)
            
            # 2. Configurar ubicación PRIMERO (antes de buscar)
            step_start = time.perf_counter()
            logger.info("Paso 2: Configurando ubicación...")
            self.configure_location(location)
            log_timing("2. Configuración de ubicación", step_start)
            
            # 3. Buscar producto
            step_start = time.perf_counter()
            logger.info("Paso 3: Buscando '{search_term}'...")
            search_box = self.scraper.wait_for_element(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='Search']")
            if search_box:
                search_box.clear()
                search_box.send_keys(search_term)
                search_box.send_keys(Keys.RETURN)
                time.sleep(5)
                logger.info("✓ Búsqueda realizada")
            log_timing("3. Búsqueda de producto", step_start)
            
            # 4. Aplicar filtros de precio
            step_start = time.perf_counter()
            logger.info("Paso 4: Aplicando filtros de precio...")
            self.apply_price_filters(min_price, max_price)
            log_timing("4. Aplicación de filtros", step_start)
            
            # 5. Procesar páginas dinámicamente
            page_num = 1
            total_extracted = 0
            
            while total_extracted < max_items:
                # Verificar si hay interrupción
                if interrupted:
                    logger.warning("⚠️  Deteniendo scraping por interrupción del usuario...")
                    break
                
                page_start = time.perf_counter()
                logger.info(f"\n{'='*60}")
                logger.info(f"PÁGINA {page_num} - Extraídos: {total_extracted}/{max_items}")
                logger.info(f"{'='*60}\n")
                
                # Obtener TODOS los enlaces de productos de la página actual
                links_start = time.perf_counter()
                product_links = self.get_product_links(max_items=999)
                log_timing(f"5.{page_num}.a Obtención de enlaces", links_start)
                
                if not product_links:
                    logger.warning(f"No se encontraron productos en página {page_num}")
                    break
                
                # Calcular cuántos productos procesar de esta página
                remaining = max_items - total_extracted
                items_to_process = min(len(product_links), remaining)
                
                logger.info(f"Items encontrados en página: {len(product_links)}")
                logger.info(f"Items a procesar: {items_to_process}\n")
                
                # Procesar cada producto
                products_start = time.perf_counter()
                for idx in range(items_to_process):
                    # Verificar interrupción en cada producto
                    if interrupted:
                        logger.warning("⚠️  Deteniendo procesamiento de productos...")
                        break
                        
                    item_start = time.perf_counter()
                    product_url = product_links[idx]
                    global_index = total_extracted + idx + 1
                    product_data = self.extract_product_details(product_url, global_index)
                    self.all_products.append(product_data)
                    log_timing(f"   Producto {global_index}", item_start)
                    
                    # Volver a la página de resultados
                    if not interrupted:  # Solo volver si no fue interrumpido
                        self.scraper.driver.back()
                        time.sleep(1)
                
                # Si hubo interrupción durante procesamiento, actualizar contador con lo procesado
                if interrupted:
                    actual_processed = len([p for p in self.all_products if p['index'] > total_extracted])
                    total_extracted += actual_processed
                    break
                
                log_timing(f"5.{page_num}.b Procesamiento de {items_to_process} productos", products_start)
                
                # Actualizar contador total
                total_extracted += items_to_process
                log_timing(f"5.{page_num} Página completa", page_start)
                logger.info(f"\n✓ Total extraído hasta ahora: {total_extracted}/{max_items}")
                
                # Si ya alcanzamos el máximo, terminar
                if total_extracted >= max_items:
                    logger.info(f"\n✓✓✓ Se alcanzó el límite de {max_items} items")
                    break
                
                # Intentar ir a la siguiente página
                page_num += 1
                logger.info(f"\nIntentando ir a página {page_num}...")
                try:
                    # Buscar botón de siguiente página
                    next_buttons = [
                        "button[aria-label*='next']",
                        "a[aria-label*='next']",
                        "button:has-text('Next')",
                        "a:has-text('Next')"
                    ]
                    
                    next_clicked = False
                    for selector in next_buttons:
                        try:
                            next_btn = self.scraper.driver.find_element(By.CSS_SELECTOR, selector)
                            if next_btn and next_btn.is_displayed():
                                next_btn.click()
                                time.sleep(2)
                                next_clicked = True
                                logger.info(f"✓ Navegando a página {page_num}")
                                break
                        except:
                            continue
                    
                    if not next_clicked:
                        logger.info("No hay más páginas disponibles")
                        break
                        
                except Exception as e:
                    logger.warning(f"Error al cambiar de página: {e}")
                    break
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Interrupción por teclado (Ctrl+C)")
            logger.info("Guardando datos recolectados antes de salir...")
        
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}")
        
        finally:
            total_time = time.perf_counter() - scraping_start
            log_timing("TOTAL SCRAPING", scraping_start)
            
            # Mostrar resumen detallado de tiempos por operación
            print_timing_summary()
            
            if interrupted:
                logger.info(f"💾 Datos recolectados antes de la interrupción: {len(self.all_products)} productos")
            
            self.scraper.close()
        
        return self.all_products


def generate_mobile_html(products, search_term, location, min_price, max_price):
    """Genera HTML optimizado para mobile con todos los productos"""
    
    # Ordenar productos por precio (de menor a mayor)
    def extract_price(product):
        price_str = product.get('price', '$0')
        # Extraer solo los números del precio
        import re
        match = re.search(r'[\d,]+', price_str)
        if match:
            return float(match.group().replace(',', ''))
        return 0
    
    sorted_products = sorted(products, key=extract_price)
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OfferUp - {search_term}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding-bottom: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header h1 {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .stats {{
            background: white;
            padding: 15px;
            margin: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 10px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .container {{
            padding: 0 15px;
        }}
        
        .product-card {{
            background: white;
            border-radius: 12px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s;
        }}
        
        .product-card:active {{
            transform: scale(0.98);
        }}
        
        .product-header {{
            position: relative;
            height: 250px;
            background: #e9ecef;
            overflow: hidden;
        }}
        
        .product-image {{
            width: 40%;
            height: 40%;
            object-fit: cover;
        }}
        
        .product-number {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }}
        
        .product-price {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: #28a745;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 20px;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}
        
        .product-content {{
            padding: 15px;
        }}
        
        .product-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        
        .product-location {{
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .product-description {{
            color: #555;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 15px;
            max-height: 100px;
            overflow: hidden;
            position: relative;
        }}
        
        .product-images {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            padding: 15px 0;
        }}
        
        .product-images::-webkit-scrollbar {{
            height: 8px;
        }}
        
        .product-images::-webkit-scrollbar-thumb {{
            background: #667eea;
            border-radius: 2px;
        }}
        
        .thumbnail {{
            width: 100%;
            height: auto;
            aspect-ratio: 1;
            border-radius: 12px;
            object-fit: cover;
            border: 3px solid #e9ecef;
        }}
        
        .product-link {{
            display: block;
            background: #667eea;
            color: white;
            text-align: center;
            padding: 12px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 10px;
        }}
        
        .product-link:active {{
            background: #5568d3;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }}
        
        @media (min-width: 768px) {{
            .container {{
                max-width: 600px;
                margin: 0 auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 {search_term}</h1>
        <div class="meta">
            📍 {location} | 💵 ${min_price:,} - ${max_price:,}
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-label">Resultados encontrados</div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">Total</div>
                <div class="stat-value">{len(products)}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Fecha</div>
                <div class="stat-value">{datetime.now().strftime('%d/%m/%Y')}</div>
            </div>
        </div>
    </div>
    
    <div class="container">
"""
    
    for idx, product in enumerate(sorted_products, 1):
        title = product.get('title', 'Sin título')
        price = product.get('price', 'N/A')
        location = product.get('location', 'Sin ubicación')
        description = product.get('description', 'Sin descripción')
        images = product.get('images', [])
        url = product.get('url', '#')
        
        # Primera imagen como principal
        main_image = images[0] if images else 'https://via.placeholder.com/800x600?text=Sin+Imagen'
        
        html += f"""
        <div class="product-card">
            <div class="product-header">
                <img src="{main_image}" alt="{title}" class="product-image" onerror="this.src='https://via.placeholder.com/800x600?text=Sin+Imagen'">
                <div class="product-number">#{idx}</div>
                <div class="product-price">{price}</div>
            </div>
            <div class="product-content">
                <h2 class="product-title">{title}</h2>
                <div class="product-location">📍 {location}</div>
                <div class="product-description">{description[:200]}{'...' if len(description) > 200 else ''}</div>
"""
        
        # Thumbnails de imágenes adicionales en grid de 2 columnas
        if len(images) > 1:
            html += '                <div class="product-images">\n'
            for img_url in images[1:6]:  # Máximo 5 thumbnails adicionales
                html += f'                    <img src="{img_url}" alt="Imagen" class="thumbnail" onerror="this.style.display=&apos;none&apos;">\n'
            html += '                </div>\n'
        
        html += f"""
                <a href="{url}" class="product-link" target="_blank">Ver en OfferUp →</a>
            </div>
        </div>
"""
    
    html += f"""
    </div>
    
    <div class="footer">
        Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
        Total de productos: {len(products)}
    </div>
</body>
</html>
"""
    return html


def create_scheduled_task(task_name, script_path, schedule_time, config):
    """Crea una tarea programada en Windows"""
    try:
        import subprocess
        import json
        
        # Guardar configuración en archivo JSON para la tarea programada
        config_file = os.path.join(os.path.dirname(script_path), 'scheduled_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # Crear script batch que ejecuta el scraper con la configuración guardada
        batch_file = os.path.join(os.path.dirname(script_path), 'run_scheduled_scraper.bat')
        venv_python = os.path.join(os.path.dirname(script_path), 'venv', 'Scripts', 'python.exe')
        
        with open(batch_file, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "{os.path.dirname(script_path)}"\n')
            f.write(f'"{venv_python}" "{script_path}" --scheduled\n')
        
        # Comando para crear tarea programada de Windows
        # Formato: schtasks /create /tn "nombre" /tr "comando" /sc DAILY /st HH:MM
        cmd = [
            'schtasks', '/create',
            '/tn', task_name,
            '/tr', f'"{batch_file}"',
            '/sc', 'DAILY',
            '/st', schedule_time,
            '/f'  # Fuerza la creación incluso si ya existe
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Tarea programada creada: {task_name}")
            logger.info(f"⏰ Se ejecutará diariamente a las {schedule_time}")
            logger.info(f"📝 Configuración guardada en: {config_file}")
            logger.info(f"\n💡 Para administrar tareas programadas:")
            logger.info(f"   - Ver: schtasks /query /tn \"{task_name}\"")
            logger.info(f"   - Eliminar: schtasks /delete /tn \"{task_name}\" /f")
            logger.info(f"   - O usa el Programador de tareas de Windows\n")
            return True
        else:
            logger.error(f"❌ Error al crear tarea programada: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al crear tarea programada: {e}")
        return False


def send_email_gmail(recipient_email, subject, html_content, html_file_path=None, sender_email=None, sender_password=None):
    """Envía email con HTML usando Gmail SMTP"""
    try:
        # Usar credenciales de .env si no se proporcionaron
        if not sender_email:
            sender_email = Config.GMAIL_USER if Config.GMAIL_USER else input("\n📧 Email de Gmail (remitente): ").strip()
        
        if not sender_password:
            sender_password = Config.GMAIL_APP_PASSWORD if Config.GMAIL_APP_PASSWORD else None
            if not sender_password:
                print("\n🔑 Contraseña de aplicación de Gmail")
                print("   (Crear en: https://myaccount.google.com/apppasswords)")
                sender_password = getpass.getpass("   Password: ")
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Adjuntar HTML como contenido
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Adjuntar archivo HTML si se especifica
        if html_file_path and os.path.exists(html_file_path):
            with open(html_file_path, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(html_file_path)}"')
                msg.attach(attachment)
        
        # Conectar y enviar
        print("\n📤 Conectando con Gmail...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email enviado exitosamente a {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al enviar email: {e}")
        return False


def get_user_input():
    """Solicita parámetros de búsqueda al usuario"""

    print("\n" + "="*60)
    print("🔍 CONFIGURACIÓN DE BÚSQUEDA EN OFFERUP")
    print("="*60 + "\n")
    
    # Término de búsqueda
    while True:
        search_term = input("📝 Término de búsqueda (ej: iphone, ford bronco): ").strip()
        if search_term:
            break
        print("❌ Por favor ingresa un término de búsqueda válido\n")
    
    # Código postal
    while True:
        zip_code = input("\n📍 Código postal / ZIP Code (ej: 92101): ").strip()
        if zip_code and len(zip_code) == 5 and zip_code.isdigit():
            break
        print("❌ Por favor ingresa un código postal válido de 5 dígitos\n")
    
    # Precio mínimo
    while True:
        try:
            min_price_input = input("\n💵 Precio mínimo en USD (Enter para $0): ").strip()
            min_price = 0 if not min_price_input else int(min_price_input)
            if min_price >= 0:
                break
            print("❌ El precio mínimo debe ser mayor o igual a 0\n")
        except ValueError:
            print("❌ Por favor ingresa un número válido\n")
    
    # Precio máximo
    while True:
        try:
            max_price_input = input(f"💵 Precio máximo en USD (Enter para sin límite): ").strip()
            max_price = 999999 if not max_price_input else int(max_price_input)
            if max_price >= min_price:
                break
            print(f"❌ El precio máximo debe ser mayor o igual al mínimo (${min_price})\n")
        except ValueError:
            print("❌ Por favor ingresa un número válido\n")
    
    # Cantidad de items
    while True:
        try:
            max_items_input = input("\n🔢 Cantidad de productos a extraer (Enter para 100): ").strip()
            max_items = 100 if not max_items_input else int(max_items_input)
            if max_items > 0:
                break
            print("❌ La cantidad debe ser mayor a 0\n")
        except ValueError:
            print("❌ Por favor ingresa un número válido\n")
    
    # Configuración de email
    send_email = input("\n📧 ¿Enviar resultados por email al finalizar? (S/n): ").strip().lower()
    send_email = send_email in ['s', 'si', 'yes', 'y', '']
    
    recipient_email = None
    if send_email:
        while True:
            recipient_email = input("📩 Email destinatario: ").strip()
            if recipient_email and '@' in recipient_email:
                break
            print("❌ Por favor ingresa un email válido\n")
    
    # Configuración de programación diaria
    schedule_daily = input("\n⏰ ¿Programar esta búsqueda diariamente? (S/n): ").strip().lower()
    schedule_daily = schedule_daily in ['s', 'si', 'yes', 'y', '']
    
    schedule_time = None
    if schedule_daily:
        while True:
            schedule_time = input("🕐 Hora de ejecución diaria (formato 24h, ej: 14:30): ").strip()
            try:
                # Validar formato HH:MM
                hours, minutes = schedule_time.split(':')
                hours, minutes = int(hours), int(minutes)
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    break
                print("❌ Hora inválida. Usa formato 24h (00:00 - 23:59)\n")
            except:
                print("❌ Formato incorrecto. Usa HH:MM (ej: 14:30)\n")
    
    # Confirmación
    print("\n" + "="*60)
    print("📋 RESUMEN DE CONFIGURACIÓN:")
    print("="*60)
    print(f"🔍 Búsqueda: {search_term}")
    print(f"📍 Ubicación: {zip_code}")
    print(f"💵 Precio: ${min_price} - ${max_price}")
    print(f"🔢 Cantidad: {max_items} productos")
    if send_email:
        print(f"📧 Email: {recipient_email}")
    if schedule_daily:
        print(f"⏰ Programación: Diaria a las {schedule_time}")
    print("="*60)
    
    confirm = input("\n✅ ¿Continuar con esta configuración? (S/n): ").strip().lower()
    if confirm and confirm not in ['s', 'si', 'yes', 'y', '']:
        print("\n❌ Operación cancelada por el usuario")
        return None
    
    return {
        'search_term': search_term,
        'zip_code': zip_code,
        'min_price': min_price,
        'max_price': max_price,
        'max_items': max_items,
        'send_email': send_email,
        'recipient_email': recipient_email,
        'schedule_daily': schedule_daily,
        'schedule_time': schedule_time
    }


def main():
    """Función principal"""
    import sys
    
    # Registrar manejador de señales para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    Config.create_directories()
    
    # Verificar si se ejecuta desde tarea programada
    is_scheduled = '--scheduled' in sys.argv
    
    if is_scheduled:
        # Cargar configuración guardada
        config_file = os.path.join(os.path.dirname(__file__), 'scheduled_config.json')
        if os.path.exists(config_file):
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("📋 Ejecutando tarea programada con configuración guardada")
        else:
            logger.error("❌ No se encontró archivo de configuración programada")
            return
    else:
        # Solicitar parámetros al usuario
        config = get_user_input()
        if not config:
            return
    
    # Crear carpeta con timestamp para esta ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join("data", f"scraping_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    logger.info(f"📁 Carpeta de salida creada: {output_folder}")
    logger.info(f"ℹ️  Presiona Ctrl+C en cualquier momento para detener y guardar datos\n")
    
    # Parámetros del usuario
    search_term = config['search_term']
    zip_code = config['zip_code']
    min_price = config['min_price']
    max_price = config['max_price']
    max_items = config['max_items']
    
    # Crear scraper
    scraper = OfferUpDetailedScraper(headless=False)
    
    # Ejecutar scraping
    results = scraper.scrape_with_pagination(
        search_term=search_term,
        location=zip_code,  # Código postal
        min_price=min_price,
        max_price=max_price,
        max_items=max_items
    )
    
    # Guardar resultados en la carpeta con timestamp (siempre, incluso si fue interrumpido)
    if results:
        save_start = time.perf_counter()
        
        filename_json = os.path.join(output_folder, f"offerup_{search_term}_detailed.json")
        filename_csv = os.path.join(output_folder, f"offerup_{search_term}_detailed.csv")
        
        logger.info(f"\n💾 Guardando {len(results)} productos...")
        save_to_json(results, filename_json)
        save_to_csv(results, filename_csv)
        
        # Generar HTML mobile-optimizado
        html_content = generate_mobile_html(results, search_term, zip_code, min_price, max_price)
        filename_html = os.path.join(output_folder, f"offerup_{search_term.replace(' ', '_')}_mobile.html")
        with open(filename_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"📱 HTML móvil guardado: {filename_html}")
        
        save_time = time.perf_counter() - save_start
        
        logger.info("\n" + "="*60)
        if interrupted:
            logger.info("⚠️  SCRAPING INTERRUMPIDO (datos guardados)")
        else:
            logger.info("✅ SCRAPING COMPLETADO")
        logger.info("="*60)
        logger.info(f"Total de productos extraídos: {len(results)}")
        logger.info(f"Carpeta de salida: {output_folder}")
        logger.info(f"Archivos guardados:")
        logger.info(f"  - {filename_json}")
        logger.info(f"  - {filename_csv}")
        logger.info(f"  - {filename_html}")
        logger.info(f"Tiempo de guardado: {save_time:.2f}s")
        logger.info("="*60 + "\n")
        
        # Enviar por email si fue configurado
        if not interrupted and config.get('send_email') and config.get('recipient_email'):
            subject = f"OfferUp - {search_term} ({len(results)} productos)"
            send_email_gmail(
                recipient_email=config['recipient_email'],
                subject=subject,
                html_content=html_content,
                html_file_path=filename_html
            )
    else:
        logger.warning("⚠️  No se extrajeron productos")
    
    # Crear tarea programada si fue configurado (solo primera vez, no desde tarea programada)
    if not interrupted and not is_scheduled and config.get('schedule_daily') and config.get('schedule_time'):
        task_name = f"OfferUp_Scraper_{search_term.replace(' ', '_')}"
        script_path = os.path.abspath(__file__)
        create_scheduled_task(task_name, script_path, config['schedule_time'], config)


if __name__ == "__main__":
    main()
