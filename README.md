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
- ✅ Exportación a CSV/JSON/HTML
- ✅ Manejo de errores y logging
- ✅ Rotating user agents
- ✅ Interfaz interactiva para configurar búsquedas
- ✅ Extracción detallada de productos (título, precio, descripción, imágenes, ubicación)
- ✅ Paginación dinámica
- ✅ HTML mobile-optimizado con diseño responsive
- ✅ Envío automático por Gmail con HTML embebido

## 📧 Configuración de Email (Gmail)

Para enviar los resultados por email, necesitas configurar una **contraseña de aplicación** de Gmail:

1. Ve a [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Inicia sesión en tu cuenta Gmail
3. Selecciona "Correo" como aplicación
4. Selecciona tu dispositivo
5. Copia la contraseña de 16 caracteres generada
6. Agrégala al archivo `.env`:
```bash
GMAIL_USER=tu_email@gmail.com
GMAIL_APP_PASSWORD=tu_password_aqui
```

**Nota**: La contraseña de aplicación es diferente a tu contraseña de Gmail normal y es más segura.

## 📱 Formato HTML Mobile

El scraper genera un archivo HTML optimizado para móviles con:
- Diseño responsive que se adapta a cualquier pantalla
- Scroll vertical continuo con todos los productos
- Cards con imágenes, precio, título, descripción y galería
- Header sticky con resumen de búsqueda
- Compatibilidad total sin necesidad de internet después de cargar
- Enlace directo a cada producto en OfferUp

## 📝 Notas

- Los datos scrapeados se guardan en el directorio `data/`
- Asegúrate de respetar los términos de servicio de los sitios web
- Implementa delays apropiados entre requests
