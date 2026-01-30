"""
Sistema de Scraping Multi-Propósito
Menú principal para ejecutar diferentes scrapers
"""
import os
import sys
import logging
from config import Config
from scraper_manager import ScraperManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clear_screen():
    """Limpia la consola"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Imprime el encabezado del menú"""
    clear_screen()
    print("\n" + "="*60)
    print(" "*15 + "SISTEMA DE WEB SCRAPING")
    print("="*60)


def print_menu(manager: ScraperManager):
    """
    Imprime el menú principal con los scrapers disponibles
    
    Args:
        manager: Instancia de ScraperManager con scrapers registrados
    """
    print("\nScrapers Disponibles:")
    print("-" * 60)
    
    scrapers = manager.list_scrapers()
    for idx, (key, scraper) in enumerate(scrapers.items(), 1):
        print(f"{idx}. {scraper['name']}")
        print(f"   → {scraper['description']}")
        print()
    
    print(f"{len(scrapers) + 1}. Salir")
    print("-" * 60)


def run_offerup_scraper():
    """Ejecuta el scraper de OfferUp"""
    from offerup_detailed_scraper import main as offerup_main
    offerup_main()


def run_clothing_image_scraper():
    """Ejecuta el scraper de imágenes de ropa"""
    from clothing_scraper import run_clothing_scraper
    print("\n" + "="*60)
    print("INICIANDO SCRAPER DE IMÁGENES DE ROPA")
    print("="*60 + "\n")
    run_clothing_scraper()


def run_tijuana_executives_scraper():
    """Ejecuta el scraper de ejecutivos de Tijuana"""
    from tijuana_executives_scraper import main as executives_main
    print("\n" + "="*60)
    print("INICIANDO SCRAPER DE EJECUTIVOS TIJUANA")
    print("="*60 + "\n")
    executives_main()


def setup_scrapers():
    """
    Configura y registra todos los scrapers disponibles
    
    Returns:
        ScraperManager con todos los scrapers registrados
    """
    manager = ScraperManager()
    
    # Registrar scraper de OfferUp
    manager.register_scraper(
        key='offerup',
        name='OfferUp Scraper',
        description='Busca y extrae información de productos en OfferUp',
        execute_func=run_offerup_scraper
    )
    
    # Registrar scraper de imágenes de ropa
    manager.register_scraper(
        key='clothing',
        name='Clothing Image Scraper',
        description='Descarga imágenes de ropa de sitios web populares',
        execute_func=run_clothing_image_scraper
    )
    
    # Registrar scraper de ejecutivos de Tijuana
    manager.register_scraper(
        key='executives',
        name='Tijuana Executives Scraper',
        description='Busca y extrae información de ejecutivos y directivos en Tijuana',
        execute_func=run_tijuana_executives_scraper
    )
    
    # Aquí puedes agregar más scrapers en el futuro
    # manager.register_scraper(
    #     key='nuevo_scraper',
    #     name='Nuevo Scraper',
    #     description='Descripción del nuevo scraper',
    #     execute_func=funcion_ejecutar_scraper
    # )
    
    return manager


def main():
    """Función principal del programa"""
    # Crear directorios necesarios
    Config.create_directories()
    
    # Configurar scrapers
    manager = setup_scrapers()
    scrapers = manager.list_scrapers()
    scraper_keys = list(scrapers.keys())
    
    while True:
        try:
            # Mostrar menú
            print_header()
            print_menu(manager)
            
            # Obtener selección del usuario
            choice = input("\nSelecciona una opción: ").strip()
            
            # Validar entrada
            if not choice.isdigit():
                print("\n⚠ Por favor ingresa un número válido")
                input("\nPresiona Enter para continuar...")
                continue
            
            choice_num = int(choice)
            
            # Opción de salir
            if choice_num == len(scrapers) + 1:
                print("\n" + "="*60)
                print(" "*15 + "¡Hasta luego!")
                print("="*60 + "\n")
                break
            
            # Validar rango
            if choice_num < 1 or choice_num > len(scrapers):
                print(f"\n⚠ Opción inválida. Selecciona entre 1 y {len(scrapers) + 1}")
                input("\nPresiona Enter para continuar...")
                continue
            
            # Ejecutar scraper seleccionado
            selected_key = scraper_keys[choice_num - 1]
            selected_scraper = scrapers[selected_key]
            
            print(f"\n✓ Has seleccionado: {selected_scraper['name']}")
            confirm = input("¿Deseas continuar? (s/n) [s]: ").strip().lower() or 's'
            
            if confirm in ['s', 'si', 'sí', 'y', 'yes']:
                try:
                    manager.execute_scraper(selected_key)
                except Exception as e:
                    logger.error(f"Error ejecutando scraper: {e}")
                    print(f"\n✗ Error: {e}")
                
                input("\n\nPresiona Enter para volver al menú principal...")
            else:
                print("\nOperación cancelada")
                input("\nPresiona Enter para continuar...")
        
        except KeyboardInterrupt:
            print("\n\n⚠ Operación interrumpida por el usuario")
            confirm_exit = input("¿Deseas salir? (s/n): ").strip().lower()
            if confirm_exit in ['s', 'si', 'sí', 'y', 'yes']:
                break
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            print(f"\n✗ Error inesperado: {e}")
            input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {e}")
        print(f"\n✗ Error fatal: {e}")
        sys.exit(1)
