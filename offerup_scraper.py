"""
Scraper específico para OfferUp
"""
import re
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from scraper import WebScraper
from utils import save_to_json, save_to_csv, log_scraping_stats, clean_text
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('offerup_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OfferUpScraper:
    """Scraper especializado para OfferUp"""
    
    def __init__(self, headless=False):
        self.scraper = WebScraper(headless=headless, timeout=15)
        self.base_url = "https://offerup.com/"
    
    def search_items(self, search_term: str, location: str = None, min_price: int = 0, max_price: int = None, max_items: int = 20):
        """
        Busca items en OfferUp
        
        Args:
            search_term: Término de búsqueda
            location: Ubicación (ej: "San Diego, CA")
            min_price: Precio mínimo (opcional)
            max_price: Precio máximo (opcional)
            max_items: Número máximo de items a extraer
            
        Returns:
            Lista de items encontrados
        """
        scraped_data = []
        start_time = time.time()
        items = []
        
        try:
            self.scraper.setup_driver()
            
            # Navegar a OfferUp
            logger.info(f"Navegando a OfferUp...")
            self.scraper.get_page(self.base_url)
            time.sleep(3)
            
            # Buscar el campo de búsqueda
            logger.info(f"Buscando: {search_term}")
            
            # Intentar encontrar el campo de búsqueda (puede variar según la versión del sitio)
            search_selectors = [
                "input[placeholder*='Search']",
                "input[type='search']",
                "input[name='q']",
                "#search-input"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.scraper.wait_for_element(By.CSS_SELECTOR, selector, timeout=5)
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                logger.error("No se pudo encontrar el campo de búsqueda")
                return []
            
            # Realizar búsqueda
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            time.sleep(5)
            
            # Configurar ubicación si se proporciona
            if location:
                logger.info(f"Intentando configurar ubicación: {location}")
                try:
                    # Buscar campo de ubicación (puede variar según la versión del sitio)
                    location_selectors = [
                        "input[placeholder*='location']",
                        "input[placeholder*='Location']",
                        "input[aria-label*='location']"
                    ]
                    
                    location_box = None
                    for selector in location_selectors:
                        try:
                            location_box = self.scraper.wait_for_element(By.CSS_SELECTOR, selector, timeout=3)
                            if location_box:
                                break
                        except:
                            continue
                    
                    if location_box:
                        location_box.clear()
                        location_box.send_keys(location)
                        time.sleep(2)
                        location_box.send_keys(Keys.RETURN)
                        time.sleep(3)
                        logger.info(f"Ubicación configurada: {location}")
                    else:
                        logger.warning("No se pudo encontrar el campo de ubicación")
                except Exception as e:
                    logger.warning(f"Error configurando ubicación: {e}")
            
            # Configurar filtros de precio si se proporcionan
            # Basado en el screenshot: hay campos de texto en el sidebar izquierdo con un botón "Go"
            if min_price is not None or max_price is not None:
                logger.info(f"Configurando filtros de precio: ${min_price} - ${max_price}")
                try:
                    time.sleep(3)  # Esperar a que cargue la página de resultados
                    
                    # Los campos están visibles en el sidebar - buscar inputs de texto
                    price_inputs = self.scraper.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    
                    min_box = None
                    max_box = None
                    
                    # Encontrar los dos primeros campos visibles (min y max precio)
                    visible_inputs = [inp for inp in price_inputs if inp.is_displayed()]
                    
                    if len(visible_inputs) >= 2:
                        min_box = visible_inputs[0]
                        max_box = visible_inputs[1]
                        
                        if min_price is not None:
                            min_box.clear()
                            min_box.send_keys(str(min_price))
                            logger.info(f"Precio mínimo: ${min_price}")
                        
                        if max_price is not None:
                            max_box.clear()
                            max_box.send_keys(str(max_price))
                            logger.info(f"Precio máximo: ${max_price}")
                        
                        time.sleep(1)
                        
                        # Buscar botón "Go" para aplicar filtros
                        go_button = self.scraper.driver.find_elements(By.XPATH, "//button[contains(text(), 'Go')]")
                        if go_button and go_button[0].is_displayed():
                            go_button[0].click()
                            logger.info("Filtros aplicados con botón Go")
                            time.sleep(3)
                        else:
                            # Si no hay botón, presionar Enter en el último campo
                            max_box.send_keys(Keys.RETURN)
                            time.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Error configurando filtros: {e}")
                    logger.info("Se aplicará filtrado manual en los resultados")
            
            # Tomar screenshot para debugging
            self.scraper.take_screenshot("offerup_search.png")
            
            # Esperar a que carguen los resultados
            logger.info("Esperando resultados...")
            
            # Scroll para cargar más items
            logger.info("Haciendo scroll para cargar más items...")
            for _ in range(3):
                self.scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Buscar elementos de items - basado en screenshot, son enlaces con clase específica
            item_selectors = [
                "a[href*='/item/']",  # Enlaces directos a items
                "div[data-testid='item-card']",
                "a[data-testid='listing-card']",
                "article"
            ]
            
            items = []
            for selector in item_selectors:
                items = self.scraper.find_elements_safe(By.CSS_SELECTOR, selector)
                if items:
                    logger.info(f"Encontrados {len(items)} items con selector: {selector}")
                    break
            
            if not items:
                logger.warning("No se encontraron items. Esto puede deberse a:")
                logger.warning("1. OfferUp requiere inicio de sesión")
                logger.warning("2. Cambios en la estructura del sitio")
                logger.warning("3. Bloqueo por detección de bot")
                logger.warning("4. Restricciones geográficas")
                
                # Guardar HTML para análisis
                with open("data/offerup_page.html", "w", encoding="utf-8") as f:
                    f.write(self.scraper.driver.page_source)
                logger.info("HTML guardado en data/offerup_page.html para análisis")
                
                return []
            
            # Limitar items
            items = items[:max_items]
            
            # Extraer datos de cada item
            for idx, item in enumerate(items, 1):
                try:
                    data = self._extract_item_data(item, idx)
                    if data:
                        # Filtrar por precio si es necesario
                        if min_price is not None or max_price is not None:
                            price_str = data.get('price', '')
                            try:
                                # Extraer número del precio (ej: "$150" -> 150)
                                price_match = re.search(r'[\d,]+', price_str.replace('$', ''))
                                if price_match:
                                    price_value = int(price_match.group().replace(',', ''))
                                    
                                    # Aplicar filtros
                                    if min_price is not None and price_value < min_price:
                                        logger.debug(f"Item filtrado por precio bajo: ${price_value}")
                                        continue
                                    if max_price is not None and price_value > max_price:
                                        logger.debug(f"Item filtrado por precio alto: ${price_value}")
                                        continue
                                    
                                    data['price_value'] = price_value
                            except:
                                pass  # Si no se puede extraer el precio, incluir el item de todos modos
                        
                        scraped_data.append(data)
                        logger.info(f"Item {idx} extraído: {data.get('title', 'N/A')} - {data.get('price', 'N/A')}")
                except Exception as e:
                    logger.error(f"Error extrayendo item {idx}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}")
        
        finally:
            self.scraper.close()
        
        # Estadísticas
        duration = time.time() - start_time
        log_scraping_stats(
            total_items=len(items) if items else 0,
            success=len(scraped_data),
            failed=(len(items) if items else 0) - len(scraped_data),
            duration=duration
        )
        
        return scraped_data
    
    def _extract_item_data(self, item, idx: int):
        """
        Extrae datos de un item individual
        
        Args:
            item: Elemento web del item
            idx: Índice del item
            
        Returns:
            Diccionario con datos del item
        """
        data = {
            "id": idx,
            "title": "",
            "price": "",
            "price_value": None,
            "location": "",
            "url": "",
            "image_url": "",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Título
            title_selectors = ["h2", "h3", "[class*='title']", "a"]
            for selector in title_selectors:
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text:
                        data["title"] = clean_text(title_elem.text)
                        break
                except:
                    continue
            
            # Precio
            price_selectors = ["[class*='price']", "span[class*='amount']"]
            for selector in price_selectors:
                try:
                    price_elem = item.find_element(By.CSS_SELECTOR, selector)
                    if price_elem and price_elem.text:
                        data["price"] = clean_text(price_elem.text)
                        break
                except:
                    continue
            
            # URL
            try:
                link = item.find_element(By.TAG_NAME, "a")
                data["url"] = link.get_attribute("href") or ""
            except:
                pass
            
            # Imagen
            try:
                img = item.find_element(By.TAG_NAME, "img")
                data["image_url"] = img.get_attribute("src") or ""
            except:
                pass
            
            # Ubicación
            location_selectors = ["[class*='location']", "[class*='seller']"]
            for selector in location_selectors:
                try:
                    loc_elem = item.find_element(By.CSS_SELECTOR, selector)
                    if loc_elem and loc_elem.text:
                        data["location"] = clean_text(loc_elem.text)
                        break
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error extrayendo detalles: {e}")
        
        return data if data["title"] or data["price"] else None


def main():
    """Función principal"""
    Config.create_directories()
    
    # Parámetros de búsqueda para OfferUp
    search_term = "iphone"
    location = "San Diego, CA"
    min_price = 0
    max_price = 500
    max_items = 30
    
    logger.info(f"Iniciando scraping de OfferUp")
    logger.info(f"Búsqueda: {search_term}")
    logger.info(f"Ubicación: {location}")
    logger.info(f"Rango de precios: ${min_price} - ${max_price}")
    
    # Crear scraper y buscar
    scraper = OfferUpScraper(headless=False)  # headless=False para ver el navegador
    results = scraper.search_items(
        search_term=search_term,
        location=location,
        min_price=min_price,
        max_price=max_price,
        max_items=max_items
    )
    
    # Guardar resultados
    if results:
        save_to_json(results, f"offerup_{search_term}.json")
        save_to_csv(results, f"offerup_{search_term}.csv")
        logger.info(f"Scraping completado. Se extrajeron {len(results)} items")
    else:
        logger.warning("No se extrajeron datos")
        logger.info("NOTA IMPORTANTE:")
        logger.info("OfferUp es un sitio complejo que puede requerir:")
        logger.info("- Inicio de sesión")
        logger.info("- Manejo de CAPTCHA")
        logger.info("- Esperas más largas")
        logger.info("- Técnicas anti-detección más avanzadas")
        logger.info("Revisa el archivo HTML guardado y los screenshots para análisis")


def run_offerup_scraper():
    """Función interactiva para ejecutar el scraper de OfferUp desde el menú principal"""
    print("\n" + "="*50)
    print("SCRAPER DE OFFERUP")
    print("="*50)
    
    Config.create_directories()
    
    # Obtener parámetros del usuario
    search_term = input("\nTérmino de búsqueda (ej: iphone, laptop, fridge) [default: iphone]: ").strip() or "iphone"
    location = input("Ubicación (ej: San Diego, CA) [default: San Diego, CA]: ").strip() or "San Diego, CA"
    
    try:
        min_price = int(input("Precio mínimo [default: 0]: ").strip() or '0')
    except ValueError:
        min_price = 0
    
    try:
        max_price_input = input("Precio máximo [default: sin límite]: ").strip()
        max_price = int(max_price_input) if max_price_input else None
    except ValueError:
        max_price = None
    
    try:
        max_items = int(input("Número máximo de items [default: 30]: ").strip() or '30')
    except ValueError:
        max_items = 30
    
    # Mostrar resumen
    print("\n" + "-"*50)
    print("RESUMEN DE LA BÚSQUEDA:")
    print("-"*50)
    print(f"Término: {search_term}")
    print(f"Ubicación: {location}")
    print(f"Precio mínimo: ${min_price}")
    print(f"Precio máximo: {'Sin límite' if max_price is None else f'${max_price}'}")
    print(f"Máximo de items: {max_items}")
    print("-"*50)
    
    confirm = input("\n¿Iniciar búsqueda? (s/n) [s]: ").strip().lower() or 's'
    
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("\nBúsqueda cancelada")
        return
    
    # Ejecutar scraping
    logger.info(f"Iniciando scraping de OfferUp")
    logger.info(f"Búsqueda: {search_term}")
    logger.info(f"Ubicación: {location}")
    
    scraper = OfferUpScraper(headless=False)
    results = scraper.search_items(
        search_term=search_term,
        location=location,
        min_price=min_price,
        max_price=max_price,
        max_items=max_items
    )
    
    # Guardar resultados
    if results:
        save_to_json(results, f"offerup_{search_term}.json")
        save_to_csv(results, f"offerup_{search_term}.csv")
        print(f"\n✓ Scraping completado exitosamente!")
        print(f"✓ Se extrajeron {len(results)} items")
    else:
        print("\n✗ No se extrajeron datos")
        print("\nNOTA IMPORTANTE:")
        print("OfferUp es un sitio complejo que puede requerir:")
        print("- Inicio de sesión")
        print("- Manejo de CAPTCHA")
        print("- Esperas más largas")
        print("- Técnicas anti-detección más avanzadas")


if __name__ == "__main__":
    main()
