# Web Scraper con Selenium

Proyecto de web scraping utilizando Selenium WebDriver para Python.

## 📋 Requisitos

- Python 3.8 o superior
- Google Chrome o Firefox instalado

## 🚀 Instalación

1. Crear un entorno virtual:
```bash
python -m venv venv
```

2. Activar el entorno virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
```

Edita el archivo `.env` con tu configuración.

## 💻 Uso

### Ejemplo básico:
```bash
python main.py
```

### Scraper personalizado:
```bash
python scraper.py --url https://example.com
```

## 📁 Estructura del Proyecto

```
.
├── main.py              # Script principal
├── scraper.py           # Clase scraper reutilizable
├── utils.py             # Funciones utilitarias
├── requirements.txt     # Dependencias
├── .env.example         # Variables de entorno de ejemplo
├── .gitignore          # Archivos ignorados por git
└── data/               # Directorio para datos scrapeados
```

## 🔧 Características

- ✅ Configuración de navegador headless
- ✅ Manejo automático de drivers (webdriver-manager)
- ✅ Esperas explícitas e implícitas
- ✅ Exportación a CSV/JSON
- ✅ Manejo de errores y logging
- ✅ Rotating user agents

## 📝 Notas

- Los datos scrapeados se guardan en el directorio `data/`
- Asegúrate de respetar los términos de servicio de los sitios web
- Implementa delays apropiados entre requests
