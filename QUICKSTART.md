# 🎯 GUÍA RÁPIDA - Sistema de Scraping

## 🚀 Ejecución Rápida

### Opción 1: Usando el archivo BAT (Windows)
```
Doble clic en: run_menu.bat
```

### Opción 2: Línea de comandos
```bash
python main.py
```

## 📋 Scrapers Disponibles

### 1️⃣ OfferUp Scraper
- **Función**: Busca productos en OfferUp
- **Parámetros**: 
  - Término de búsqueda
  - Ubicación
  - Rango de precios
  - Cantidad de items
- **Salida**: JSON + CSV

### 2️⃣ Clothing Image Scraper
- **Función**: Descarga imágenes de ropa
- **Sitios**: Unsplash, Pexels
- **Parámetros**:
  - Tipo de ropa
  - Cantidad de imágenes
- **Salida**: Carpeta con imágenes + JSON con metadatos

## 🛠️ Archivos Principales

| Archivo | Descripción |
|---------|-------------|
| `main.py` | 🎮 Menú principal interactivo |
| `scraper_manager.py` | 🔧 Gestor de scrapers |
| `offerup_scraper.py` | 🛒 Scraper de OfferUp |
| `clothing_scraper.py` | 👗 Scraper de imágenes de ropa |
| `config.py` | ⚙️ Configuración del sistema |
| `run_menu.bat` | 🚀 Launcher de Windows |

## 📁 Estructura de Salida

```
data/
├── scraping_YYYYMMDD_HHMMSS/     # Resultados de OfferUp
│   ├── offerup_*.csv
│   ├── offerup_*.json
│   └── offerup_*.html
│
└── clothing_YYYYMMDD_HHMMSS/     # Resultados de Clothing
    ├── images/
    │   ├── dress_1.jpg
    │   ├── dress_2.jpg
    │   └── ...
    └── clothing_*_info.json
```

## ➕ Agregar Nuevo Scraper

### Paso 1: Crear archivo `mi_scraper.py`
```python
def run_mi_scraper():
    print("Mi scraper funcionando!")
    # Tu código aquí
```

### Paso 2: Registrar en `main.py`
```python
# En setup_scrapers()
manager.register_scraper(
    key='mi_scraper',
    name='Mi Scraper',
    description='Lo que hace mi scraper',
    execute_func=run_mi_scraper
)
```

### Paso 3: Importar en `main.py`
```python
from mi_scraper import run_mi_scraper
```

¡Listo! Tu scraper aparecerá en el menú.

## 🔍 Verificación del Sistema

```bash
python test_system.py
```

## 📚 Documentación Completa

Ver: [README_MENU.md](README_MENU.md)

## ⚡ Ejemplos de Uso

### Ejemplo 1: Buscar iPhones en OfferUp
1. Ejecutar `python main.py`
2. Seleccionar opción `1` (OfferUp Scraper)
3. Ingresar:
   - Término: `iphone`
   - Ubicación: `San Diego, CA`
   - Precio min: `200`
   - Precio max: `800`
   - Items: `30`

### Ejemplo 2: Descargar imágenes de vestidos
1. Ejecutar `python main.py`
2. Seleccionar opción `2` (Clothing Image Scraper)
3. Ingresar:
   - Sitio: `1` (Unsplash)
   - Término: `dress`
   - Imágenes: `20`

## 🎨 Características

✅ Menú interactivo amigable  
✅ Sistema modular y extensible  
✅ Logs detallados  
✅ Múltiples formatos de salida  
✅ Manejo de errores robusto  
✅ Fácil de agregar nuevos scrapers  

## 📞 Soporte

Para problemas o dudas:
1. Revisar los archivos de log en `logs/`
2. Verificar el sistema con `test_system.py`
3. Consultar [README_MENU.md](README_MENU.md)
