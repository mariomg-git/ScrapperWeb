from offerup_detailed_scraper import generate_mobile_html
from datetime import datetime

# Datos de prueba
products = [
    {
        'title': 'iPhone 14 Pro Max',
        'price': '$450',
        'location': 'San Diego, CA',
        'description': 'Excelente condición, batería al 95%, sin rayones, incluye cargador original y funda de regalo.',
        'images': [
            'https://images.unsplash.com/photo-1678685888221-cda773a3dcdb?w=800',
            'https://images.unsplash.com/photo-1592286927505-c1e8394b0e1f?w=800',
            'https://images.unsplash.com/photo-1611472173362-3f53dbd65d80?w=800'
        ],
        'url': 'https://offerup.com/item/1'
    },
    {
        'title': 'Ford Bronco 2023',
        'price': '$35,000',
        'location': 'San Diego, CA',
        'description': 'Como nuevo, solo 5000 millas, mantenimiento al día.',
        'images': [
            'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=800',
            'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800'
        ],
        'url': 'https://offerup.com/item/2'
    }
]

html = generate_mobile_html(products, 'iPhone', 'San Diego', 0, 500)
with open('test_slider.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('✅ Archivo test_slider.html creado correctamente')
print('📱 Abre el archivo en tu navegador para ver el slider en acción')
