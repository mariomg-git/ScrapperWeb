# Sistema de Web Scraping Multi-Propósito

Sistema centralizado de web scraping con menú interactivo para ejecutar diferentes scrapers.

## 📋 Descripción

Este sistema proporciona una interfaz de menú unificada para ejecutar múltiples scrapers especializados. Actualmente incluye:

1. **OfferUp Scraper** - Extrae información de productos de OfferUp
2. **Clothing Image Scraper** - Descarga imágenes de ropa de sitios web populares

## 🚀 Inicio Rápido

### Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar el menú principal:
```bash
python main.py
```

## 📖 Uso del Sistema

### Menú Principal

Al ejecutar `main.py`, se mostrará un menú interactivo:

```
============================================================
               SISTEMA DE WEB SCRAPING
============================================================

Scrapers Disponibles:
------------------------------------------------------------
1. OfferUp Scraper
   → Busca y extrae información de productos en OfferUp

2. Clothing Image Scraper
   → Descarga imágenes de ropa de sitios web populares

3. Salir
------------------------------------------------------------

Selecciona una opción:
```

### Opciones del Menú

#### 1. OfferUp Scraper

Busca productos en OfferUp con los siguientes parámetros:

- **Término de búsqueda**: Producto a buscar (ej: iphone, laptop, fridge)
- **Ubicación**: Ubicación geográfica (ej: San Diego, CA)
- **Precio mínimo**: Precio mínimo del producto
- **Precio máximo**: Precio máximo del producto
- **Máximo de items**: Número máximo de resultados

**Ejemplo de uso:**
```
Término de búsqueda: laptop
Ubicación: San Diego, CA
Precio mínimo: 200
Precio máximo: 800
Número máximo de items: 30
```

**Salida:**
- `offerup_laptop.json` - Datos en formato JSON
- `offerup_laptop.csv` - Datos en formato CSV
- Screenshots y HTML guardados en carpeta `data/`

#### 2. Clothing Image Scraper

Descarga imágenes de ropa de sitios web populares:

**Sitios disponibles:**
1. Unsplash - Fashion
2. Pexels - Clothing

**Parámetros:**
- **Sitio**: Seleccionar el sitio fuente (1 o 2)
- **Término de búsqueda**: Tipo de ropa (ej: dress, jacket, fashion)
- **Número de imágenes**: Cantidad máxima de imágenes a descargar

**Ejemplo de uso:**
```
Sitio: 1 (Unsplash)
Término de búsqueda: dress
Número máximo de imágenes: 20
```

**Salida:**
- Carpeta `data/clothing_TIMESTAMP/images/` - Imágenes descargadas
- `clothing_dress_info.json` - Metadatos de las imágenes

## 🏗️ Estructura del Proyecto

```
Selenium/
├── main.py                      # Menú principal
├── scraper_manager.py           # Gestor de scrapers
├── config.py                    # Configuración general
├── offerup_scraper.py          # Scraper de OfferUp
├── clothing_scraper.py         # Scraper de imágenes de ropa
├── scraper.py                  # Clase base WebScraper
├── utils.py                    # Utilidades
├── requirements.txt            # Dependencias
├── data/                       # Datos extraídos
│   ├── scraping_*/            # Resultados de OfferUp
│   └── clothing_*/            # Imágenes de ropa
└── logs/                       # Archivos de log
```

## 🔧 Agregar Nuevos Scrapers

Para agregar un nuevo scraper al sistema:

### 1. Crear el archivo del scraper

Ejemplo: `my_scraper.py`

```python
"""
Mi nuevo scraper
"""
import logging
from scraper import WebScraper
from config import Config

logger = logging.getLogger(__name__)

class MyNewScraper:
    def __init__(self, headless=False):
        self.scraper = WebScraper(headless=headless)
    
    def scrape_data(self):
        # Implementar lógica de scraping
        pass

def run_my_scraper():
    """Función interactiva para ejecutar desde el menú"""
    print("\\n" + "="*50)
    print("MI NUEVO SCRAPER")
    print("="*50 + "\\n")
    
    # Obtener parámetros del usuario
    param1 = input("Parámetro 1: ").strip()
    
    # Ejecutar scraping
    scraper = MyNewScraper(headless=False)
    results = scraper.scrape_data()
    
    # Mostrar resultados
    if results:
        print(f"\\n✓ Scraping completado!")
    else:
        print("\\n✗ No se obtuvieron resultados")

if __name__ == "__main__":
    run_my_scraper()
```

### 2. Registrar el scraper en main.py

En la función `setup_scrapers()` de [main.py](main.py), agregar:

```python
def setup_scrapers():
    manager = ScraperManager()
    
    # ... scrapers existentes ...
    
    # Registrar nuevo scraper
    manager.register_scraper(
        key='my_scraper',
        name='Mi Nuevo Scraper',
        description='Descripción de lo que hace mi scraper',
        execute_func=run_my_scraper  # Importar función
    )
    
    return manager
```

### 3. Importar la función en main.py

Al inicio de [main.py](main.py):

```python
from my_scraper import run_my_scraper
```

### 4. (Opcional) Agregar configuración en config.py

En [config.py](config.py), dentro del diccionario `SCRAPERS`:

```python
SCRAPERS = {
    # ... scrapers existentes ...
    'my_scraper': {
        'name': 'Mi Nuevo Scraper',
        'description': 'Descripción detallada',
        'default_headless': False,
        # Parámetros personalizados
        'param1': 'valor1'
    }
}
```

## 📊 Formatos de Salida

### JSON
```json
[
    {
        "id": 1,
        "title": "Ejemplo",
        "price": "$100",
        "location": "San Diego, CA",
        "timestamp": "2025-12-19T10:30:00"
    }
]
```

### CSV
```csv
id,title,price,location,timestamp
1,Ejemplo,$100,"San Diego, CA",2025-12-19T10:30:00
```

## 🔍 Logs

Cada scraper genera su propio archivo de log:

- `main_scraper.log` - Log del menú principal
- `offerup_scraper.log` - Log del scraper de OfferUp
- `clothing_scraper.log` - Log del scraper de ropa

## ⚙️ Configuración

Editar [config.py](config.py) para ajustar:

```python
class Config:
    # Navegador
    HEADLESS = True  # Ejecutar sin interfaz gráfica
    BROWSER = "chrome"  # chrome o firefox
    TIMEOUT = 10  # Tiempo de espera en segundos
    
    # Directorios
    OUTPUT_DIR = "data"
    LOG_DIR = "logs"
    
    # Delays
    MIN_DELAY = 1
    MAX_DELAY = 3
    SCROLL_PAUSE = 1.5
```

## 🛡️ Consideraciones Importantes

### OfferUp Scraper
- Sitio complejo que puede requerir inicio de sesión
- Puede encontrar CAPTCHAs
- Requiere técnicas anti-detección
- Los selectores pueden cambiar con actualizaciones del sitio

### Clothing Image Scraper
- Respeta los términos de servicio de los sitios
- Las URLs de imágenes pueden cambiar
- Incluye delays para no sobrecargar servidores
- Verifica que tengas permiso para descargar imágenes

## 📝 Dependencias

```
selenium==4.16.0
webdriver-manager==4.0.1
pandas
python-dotenv==1.0.0
beautifulsoup4==4.12.2
openpyxl
requests==2.31.0
```

## 🤝 Contribuir

Para agregar nuevos scrapers o mejorar los existentes:

1. Crear el scraper siguiendo la estructura descrita
2. Probar exhaustivamente
3. Documentar parámetros y salidas
4. Registrar en el sistema de menús

## 📄 Licencia

Este proyecto es de código abierto para propósitos educativos.

## ⚠️ Disclaimer

Este software es solo para propósitos educativos. Asegúrate de:
- Revisar y cumplir con los términos de servicio de cada sitio
- Respetar los archivos robots.txt
- No sobrecargar los servidores con peticiones excesivas
- Obtener permiso antes de scrapear sitios comerciales
