"""
Script de ejemplo rápido para probar el sistema de menú
"""

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VERIFICACIÓN DEL SISTEMA DE SCRAPING")
    print("="*60)
    
    # Verificar que se pueden importar todos los módulos
    print("\n📦 Verificando módulos...")
    
    try:
        from scraper_manager import ScraperManager
        print("✓ scraper_manager importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando scraper_manager: {e}")
    
    try:
        from config import Config
        print("✓ config importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando config: {e}")
    
    try:
        from offerup_scraper import OfferUpScraper, run_offerup_scraper
        print("✓ offerup_scraper importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando offerup_scraper: {e}")
    
    try:
        from clothing_scraper import ClothingScraper, run_clothing_scraper
        print("✓ clothing_scraper importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando clothing_scraper: {e}")
    
    # Verificar que se pueden crear directorios
    print("\n📁 Verificando directorios...")
    try:
        Config.create_directories()
        print("✓ Directorios creados correctamente")
    except Exception as e:
        print(f"✗ Error creando directorios: {e}")
    
    # Verificar que el ScraperManager funciona
    print("\n🔧 Verificando ScraperManager...")
    try:
        manager = ScraperManager()
        manager.register_scraper(
            key='test',
            name='Test Scraper',
            description='Scraper de prueba',
            execute_func=lambda: print("Test ejecutado")
        )
        scrapers = manager.list_scrapers()
        if 'test' in scrapers:
            print("✓ ScraperManager funciona correctamente")
            print(f"  - Scrapers registrados: {len(scrapers)}")
        else:
            print("✗ Error: No se registró el scraper de prueba")
    except Exception as e:
        print(f"✗ Error con ScraperManager: {e}")
    
    print("\n" + "="*60)
    print("SISTEMA LISTO PARA USAR")
    print("="*60)
    print("\n👉 Ejecuta 'python main.py' para iniciar el menú principal\n")
