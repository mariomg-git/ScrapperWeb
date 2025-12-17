"""
Script para grabar acciones en OfferUp tipo macro
Registra todos los clics, inputs y navegación
"""
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class ActionRecorder:
    """Graba acciones del usuario para reproducirlas después"""
    
    def __init__(self):
        self.actions = []
        self.driver = None
        
    def setup_driver(self):
        """Configura Chrome con capacidad de grabar acciones"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Inyectar JavaScript para capturar eventos
        self.inject_event_listeners()
        
        return self.driver
    
    def inject_event_listeners(self):
        """Inyecta JavaScript para capturar clics e inputs"""
        js_code = """
        window.recordedActions = [];
        
        // Capturar clics
        document.addEventListener('click', function(e) {
            const action = {
                type: 'click',
                timestamp: new Date().toISOString(),
                element: {
                    tag: e.target.tagName,
                    id: e.target.id,
                    className: e.target.className,
                    text: e.target.innerText?.substring(0, 50),
                    xpath: getXPath(e.target)
                }
            };
            window.recordedActions.push(action);
            console.log('Click recorded:', action);
        }, true);
        
        // Capturar inputs
        document.addEventListener('input', function(e) {
            const action = {
                type: 'input',
                timestamp: new Date().toISOString(),
                element: {
                    tag: e.target.tagName,
                    id: e.target.id,
                    className: e.target.className,
                    value: e.target.value,
                    xpath: getXPath(e.target)
                }
            };
            window.recordedActions.push(action);
            console.log('Input recorded:', action);
        }, true);
        
        // Función para obtener XPath
        function getXPath(element) {
            if (element.id !== '')
                return 'id("' + element.id + '")';
            if (element === document.body)
                return element.tagName;
            
            var ix = 0;
            var siblings = element.parentNode.childNodes;
            for (var i = 0; i < siblings.length; i++) {
                var sibling = siblings[i];
                if (sibling === element)
                    return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                    ix++;
            }
        }
        """
        self.driver.execute_script(js_code)
    
    def start_recording(self, url):
        """Inicia la grabación navegando a la URL"""
        print(f"\n{'='*60}")
        print("GRABADOR DE ACCIONES - OfferUp Scraper")
        print(f"{'='*60}\n")
        print(f"Navegando a: {url}")
        print("\n📹 GRABACIÓN INICIADA")
        print("\nRealiza las siguientes acciones manualmente:")
        print("  1. Buscar 'iphone' en el campo de búsqueda")
        print("  2. Configurar ubicación 'San Diego, CA'")
        print("  3. Configurar precio mínimo: 0")
        print("  4. Configurar precio máximo: 500")
        print("  5. Hacer clic en 'Go' para aplicar filtros")
        print("\nPresiona Ctrl+C en la terminal cuando termines\n")
        
        self.driver.get(url)
        time.sleep(2)
        self.inject_event_listeners()  # Re-inyectar después de cargar la página
        
        try:
            # Esperar que el usuario realice acciones
            input("\nPresiona Enter cuando hayas terminado de realizar las acciones...\n")
        except KeyboardInterrupt:
            print("\n\n🛑 Grabación detenida")
    
    def get_recorded_actions(self):
        """Obtiene las acciones grabadas del navegador"""
        actions = self.driver.execute_script("return window.recordedActions || [];")
        self.actions = actions
        return actions
    
    def save_actions(self, filename='recorded_actions.json'):
        """Guarda las acciones en un archivo JSON"""
        actions = self.get_recorded_actions()
        
        data = {
            'recorded_at': datetime.now().isoformat(),
            'total_actions': len(actions),
            'actions': actions
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Acciones grabadas: {len(actions)}")
        print(f"📁 Guardado en: {filename}\n")
        return filename
    
    def replay_actions(self, filename='recorded_actions.json'):
        """Reproduce las acciones grabadas"""
        print("\n🔄 Reproduciendo acciones...\n")
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        actions = data.get('actions', [])
        
        for i, action in enumerate(actions, 1):
            try:
                print(f"[{i}/{len(actions)}] {action['type'].upper()}: {action['element']['tag']}")
                
                # Buscar elemento
                if action['element'].get('id'):
                    element = self.driver.find_element(By.ID, action['element']['id'])
                elif action['element'].get('xpath'):
                    element = self.driver.find_element(By.XPATH, action['element']['xpath'])
                else:
                    continue
                
                # Ejecutar acción
                if action['type'] == 'click':
                    element.click()
                    time.sleep(0.5)
                elif action['type'] == 'input':
                    element.clear()
                    element.send_keys(action['element']['value'])
                    time.sleep(0.3)
                
            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                continue
        
        print("\n✅ Reproducción completada\n")
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()


def main():
    """Función principal"""
    recorder = ActionRecorder()
    
    try:
        recorder.setup_driver()
        recorder.start_recording("https://offerup.com/")
        
        # Esperar un momento para que se carguen todas las acciones
        time.sleep(2)
        
        # Guardar acciones
        filename = recorder.save_actions()
        
        # Preguntar si quiere reproducir
        replay = input("\n¿Quieres reproducir las acciones ahora? (s/n): ")
        if replay.lower() == 's':
            recorder.driver.get("https://offerup.com/")
            time.sleep(2)
            recorder.inject_event_listeners()
            recorder.replay_actions(filename)
            input("\nPresiona Enter para cerrar el navegador...")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Programa interrumpido")
    finally:
        recorder.close()
        print("\n👋 Grabador cerrado\n")


if __name__ == "__main__":
    main()
