"""
Scraper para imágenes de ropa de sitios web
"""
import os
import time
import logging
import requests
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from scraper import WebScraper
from utils import save_to_json, clean_text
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clothing_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ClothingScraper:
    """Scraper especializado para imágenes de ropa"""
    
    def __init__(self, headless=False):
        self.scraper = WebScraper(headless=headless, timeout=15)
        # URLs de sitios populares de ropa (puedes modificar estas URLs)
        self.sites = {
            '1': {
                'name': 'Zara',
                'url': 'https://www.zara.com/us/',
                'base_url': 'https://www.zara.com',
                'image_selector': 'img.media-image__image',
                'title_selector': 'img'
            },
            '2': {
                'name': 'Unsplash - Fashion',
                'url': 'https://unsplash.com/s/photos/fashion',
                'image_selector': 'img[srcset]',
                'title_selector': 'img'
            },
            '3': {
                'name': 'Pexels - Clothing',
                'url': 'https://www.pexels.com/search/clothing/',
                'image_selector': 'img.photo-item__img',
                'title_selector': 'img'
            }
        }
    
    def download_image(self, url: str, save_path: str):
        """
        Descarga una imagen desde una URL
        
        Args:
            url: URL de la imagen
            save_path: Ruta donde guardar la imagen
        """
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Imagen descargada: {save_path}")
                return True
            else:
                logger.warning(f"Error descargando imagen: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
            return False
    
    def scrape_clothing_images(self, site_key: str = '1', search_term: str = 'fashion', max_images: int = 20):
        """
        Busca y descarga imágenes de ropa
        
        Args:
            site_key: Clave del sitio a scrapear (1=Zara, 2=Unsplash, 3=Pexels)
            search_term: Término de búsqueda (ej: 'dress', 'jacket', 'woman')
            max_images: Número máximo de imágenes a descargar
            
        Returns:
            Lista de información de imágenes descargadas
        """
        if site_key not in self.sites:
            logger.error(f"Sitio no válido: {site_key}")
            return []
        
        site = self.sites[site_key]
        scraped_data = []
        start_time = time.time()
        
        # Crear directorio para imágenes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(Config.OUTPUT_DIR, f"clothing_{timestamp}")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        try:
            self.scraper.setup_driver()
            
            # Construir URL de búsqueda según el sitio
            if site_key == '1':  # Zara
                # Para Zara, usar categorías específicas o búsqueda
                if search_term.lower() in ['woman', 'mujer', 'women']:
                    search_url = "https://www.zara.com/us/en/woman-l1050.html"
                elif search_term.lower() in ['man', 'hombre', 'men']:
                    search_url = "https://www.zara.com/us/en/man-l1040.html"
                elif search_term.lower() in ['kids', 'niños', 'children']:
                    search_url = "https://www.zara.com/us/en/kids-l1176.html"
                else:
                    # Usar página principal y búsqueda
                    search_url = f"https://www.zara.com/us/en/search?searchTerm={search_term}"
            elif site_key == '2':  # Unsplash
                search_url = f"https://unsplash.com/s/photos/{search_term}"
            elif site_key == '3':  # Pexels
                search_url = f"https://www.pexels.com/search/{search_term}/"
            else:
                search_url = site['url']
            
            logger.info(f"Buscando imágenes en: {site['name']}")
            logger.info(f"URL: {search_url}")
            
            if not self.scraper.get_page(search_url):
                logger.error("No se pudo cargar la página")
                return scraped_data
            
            # Esperar a que carguen las imágenes
            time.sleep(5)
            
            # Hacer scroll para cargar más imágenes
            logger.info("Haciendo scroll para cargar más imágenes...")
            scroll_count = 5 if site_key == '1' else 3  # Más scroll para Zara
            for i in range(scroll_count):
                self.scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Encontrar todas las imágenes
            images = self.scraper.find_elements_safe(By.TAG_NAME, "img")
            logger.info(f"Se encontraron {len(images)} imágenes en total")
            
            # Procesar imágenes
            downloaded_count = 0
            for idx, img in enumerate(images):
                if downloaded_count >= max_images:
                    break
                
                try:
                    # Obtener URL de la imagen
                    img_url = img.get_attribute('src')
                    if not img_url or img_url.startswith('data:'):
                        # Intentar obtener de srcset
                        srcset = img.get_attribute('srcset')
                        if srcset:
                            # Tomar la primera URL del srcset
                            img_url = srcset.split(',')[0].split(' ')[0]
                        else:
                            continue
                    
                    # Convertir URLs relativas a absolutas (importante para Zara)
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/') and site_key == '1':
                        img_url = site['base_url'] + img_url
                    
                    # Filtrar imágenes pequeñas o irrelevantes
                    if any(skip in img_url.lower() for skip in ['logo', 'icon', 'avatar', 'badge', 'sprite']):
                        continue
                    
                    # Para Zara, filtrar solo imágenes de productos
                    if site_key == '1' and not any(x in img_url for x in ['.jpg', '.jpeg', '.png', '.webp']):
                        continue
                    
                    # Obtener alt text como descripción
                    alt_text = img.get_attribute('alt') or f"clothing_image_{idx}"
                    
                    # Nombre de archivo
                    file_extension = 'jpg'
                    if '.png' in img_url.lower():
                        file_extension = 'png'
                    elif '.webp' in img_url.lower():
                        file_extension = 'webp'
                    
                    filename = f"{search_term}_{downloaded_count + 1}.{file_extension}"
                    save_path = os.path.join(images_dir, filename)
                    
                    # Descargar imagen
                    if self.download_image(img_url, save_path):
                        image_info = {
                            'id': downloaded_count + 1,
                            'filename': filename,
                            'path': save_path,
                            'url': img_url,
                            'description': clean_text(alt_text),
                            'search_term': search_term,
                            'source': site['name'],
                            'timestamp': datetime.now().isoformat()
                        }
                        scraped_data.append(image_info)
                        downloaded_count += 1
                        logger.info(f"Imagen {downloaded_count}/{max_images}: {filename}")
                    
                    time.sleep(0.5)  # Pequeña pausa entre descargas
                    
                except Exception as e:
                    logger.warning(f"Error procesando imagen {idx}: {e}")
                    continue
            
            # Guardar información en JSON
            json_file = os.path.join(output_dir, f"clothing_{search_term}_info.json")
            save_to_json(scraped_data, json_file)
            
            # Log de estadísticas
            elapsed_time = time.time() - start_time
            logger.info(f"\n{'='*50}")
            logger.info(f"RESUMEN DE SCRAPING DE ROPA")
            logger.info(f"{'='*50}")
            logger.info(f"Sitio: {site['name']}")
            logger.info(f"Término de búsqueda: {search_term}")
            logger.info(f"Imágenes descargadas: {len(scraped_data)}")
            logger.info(f"Directorio: {images_dir}")
            logger.info(f"Tiempo total: {elapsed_time:.2f} segundos")
            logger.info(f"{'='*50}\n")
            
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}")
        finally:
            self.scraper.quit()
        
        return scraped_data
    
    def list_available_sites(self):
        """Muestra los sitios disponibles para scrapear"""
        print("\nSitios disponibles:")
        for key, site in self.sites.items():
            print(f"{key}. {site['name']}")


def run_clothing_scraper():
    """Función principal para ejecutar el scraper de ropa"""
    print("\n" + "="*50)
    print("SCRAPER DE IMÁGENES DE ROPA")
    print("="*50)
    
    scraper = ClothingScraper(headless=False)
    
    # Mostrar sitios disponibles
    scraper.list_available_sites()
    
    # Obtener entrada del usuario
    site_key = input("\nSelecciona el sitio (1-3) [default: 1]: ").strip() or '1'
    
    # Sugerencias específicas para Zara
    if site_key == '1':
        print("\n💡 Sugerencias para Zara:")
        print("  - woman/mujer: Sección de mujer")
        print("  - man/hombre: Sección de hombre")
        print("  - kids/niños: Sección de niños")
        print("  - O escribe cualquier término de búsqueda")
        search_term = input("\nTérmino de búsqueda [default: woman]: ").strip() or 'woman'
    else:
        search_term = input("Término de búsqueda (ej: dress, jacket, fashion) [default: fashion]: ").strip() or 'fashion'
    
    try:
        max_images = int(input("Número máximo de imágenes a descargar [default: 20]: ").strip() or '20')
    except ValueError:
        max_images = 20
    
    # Ejecutar scraping
    results = scraper.scrape_clothing_images(
        site_key=site_key,
        search_term=search_term,
        max_images=max_images
    )
    
    if results:
        print(f"\n✓ Scraping completado exitosamente!")
        print(f"✓ {len(results)} imágenes descargadas")
    else:
        print("\n✗ No se pudieron descargar imágenes")


if __name__ == "__main__":
    run_clothing_scraper()
