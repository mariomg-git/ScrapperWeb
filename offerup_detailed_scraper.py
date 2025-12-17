"""
Scraper detallado de OfferUp - Entra a cada producto individual
"""
import re
import time
import logging
import os
from datetime import datetime
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
            self.scraper.driver.get(product_url)
            time.sleep(2)  # Reducido de 4s a 2s
            
            # Obtener todo el texto de la página para extraer información
            page_text = self.scraper.driver.find_element(By.TAG_NAME, "body").text
            
            # Título - Usar el título de la página como fallback
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
            
            # Precio - buscar en el texto de la página
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
            
            # Descripción - buscar en múltiples lugares
            desc_selectors = [
                "[data-testid='item-description']",
                "div[class*='description']",
                "p[class*='description']",
                "pre"
            ]
            for selector in desc_selectors:
                try:
                    desc_elem = self.scraper.driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem and desc_elem.text and len(desc_elem.text) > 20:
                        product_data["description"] = clean_text(desc_elem.text)[:500]  # Limitar a 500 caracteres
                        logger.info(f"  Descripción: {len(product_data['description'])} caracteres")
                        break
                except:
                    continue
            
            # Extraer ubicación del texto
            if "San Diego" in page_text or "CA" in page_text:
                # Buscar patrón de ubicación
                location_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})', page_text)
                if location_match:
                    product_data["location"] = location_match.group(1)
            
            # Imágenes
            try:
                img_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, "img")
                for img in img_elements[:5]:
                    src = img.get_attribute('src')
                    if src and ('offerup' in src or 'cloudfront' in src) and src.startswith('http'):
                        product_data["images"].append(src)
                if product_data["images"]:
                    logger.info(f"  Imágenes: {len(product_data['images'])} encontradas")
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
        
        try:
            self.scraper.setup_driver()
            
            # 1. Navegar a OfferUp
            logger.info("Paso 1: Navegando a OfferUp...")
            self.scraper.get_page(self.base_url)
            logger.info("⏳ Esperando 20 segundos para que cargue completamente...")
            time.sleep(20)  # Delay de 20 segundos para carga completa
            
            # 2. Configurar ubicación PRIMERO (antes de buscar)
            logger.info("Paso 2: Configurando ubicación...")
            self.configure_location(location)
            
            # 3. Buscar producto
            logger.info("Paso 3: Buscando '{search_term}'...")
            search_box = self.scraper.wait_for_element(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='Search']")
            if search_box:
                search_box.clear()
                search_box.send_keys(search_term)
                search_box.send_keys(Keys.RETURN)
                time.sleep(5)
                logger.info("✓ Búsqueda realizada")
            
            # 4. Aplicar filtros de precio
            logger.info("Paso 4: Aplicando filtros de precio...")
            self.apply_price_filters(min_price, max_price)
            
            # 5. Procesar páginas dinámicamente
            page_num = 1
            total_extracted = 0
            
            while total_extracted < max_items:
                logger.info(f"\n{'='*60}")
                logger.info(f"PÁGINA {page_num} - Extraídos: {total_extracted}/{max_items}")
                logger.info(f"{'='*60}\n")
                
                # Obtener TODOS los enlaces de productos de la página actual
                product_links = self.get_product_links(max_items=999)  # Sin límite por página
                
                if not product_links:
                    logger.warning(f"No se encontraron productos en página {page_num}")
                    break
                
                # Calcular cuántos productos procesar de esta página
                remaining = max_items - total_extracted
                items_to_process = min(len(product_links), remaining)
                
                logger.info(f"Items encontrados en página: {len(product_links)}")
                logger.info(f"Items a procesar: {items_to_process}\n")
                
                # Procesar cada producto
                for idx in range(items_to_process):
                    product_url = product_links[idx]
                    global_index = total_extracted + idx + 1
                    product_data = self.extract_product_details(product_url, global_index)
                    self.all_products.append(product_data)
                    
                    # Volver a la página de resultados
                    self.scraper.driver.back()
                    time.sleep(1)
                
                # Actualizar contador total
                total_extracted += items_to_process
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
            
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}")
        
        finally:
            self.scraper.close()
        
        return self.all_products


def main():
    """Función principal"""
    Config.create_directories()
    
    # Crear carpeta con timestamp para esta ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join("data", f"scraping_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    logger.info(f"Carpeta de salida: {output_folder}")
    
    # Parámetros
    search_term = "iphone"
    zip_code = "92101"  # Código postal de San Diego
    min_price = 0
    max_price = 500
    max_items = 100  # Total de items a extraer
    
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
    
    # Guardar resultados en la carpeta con timestamp
    if results:
        filename_json = os.path.join(output_folder, f"offerup_{search_term}_detailed.json")
        filename_csv = os.path.join(output_folder, f"offerup_{search_term}_detailed.csv")
        
        save_to_json(results, filename_json)
        save_to_csv(results, filename_csv)
        
        logger.info("\n" + "="*60)
        logger.info("SCRAPING COMPLETADO")
        logger.info("="*60)
        logger.info(f"Total de productos extraídos: {len(results)}")
        logger.info(f"Carpeta de salida: {output_folder}")
        logger.info(f"Archivos guardados:")
        logger.info(f"  - {filename_json}")
        logger.info(f"  - {filename_csv}")
        logger.info("="*60 + "\n")
    else:
        logger.warning("No se extrajeron productos")


if __name__ == "__main__":
    main()
