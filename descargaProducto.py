import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# URL base de la página de productos
base_url = "https://platanitos.com/pe/productos?filter_brand[]=Under+Armour&sort=timestamp_active_unix+desc&start={}" 

# Encabezados para simular un navegador
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Lista para almacenar todos los enlaces de productos
product_links = []

# Número total de productos y paginación
total_products = 656  # Basado en la información obtenida
products_per_page = 48  # Cantidad de productos por página

# Iterar sobre todas las páginas
for start in range(0, total_products, products_per_page):
    url = base_url.format(start)
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Encontrar todos los enlaces de productos
        for a_tag in soup.find_all("a", href=True):
            if "/pe/producto/" in a_tag["href"]:
                full_url = "https://platanitos.com" + a_tag["href"]
                product_links.append(full_url)
    else:
        print(f"Error al acceder a la página {url}. Código de estado: {response.status_code}")

# Eliminar duplicados
product_links = list(set(product_links))

# Guardar en un archivo Excel con la fecha y hora actual
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"URLs_Productos_{timestamp}.xlsx"
df = pd.DataFrame(product_links, columns=["URLs"])
df.to_excel(filename, index=False)

print(f"Archivo guardado: {filename}")
