import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import concurrent.futures
import re

# Encabezados para simular un navegador
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# URL base para paginación
base_url = "https://platanitos.com/pe/productos?filter_brand[]=Under+Armour&sort=timestamp_active_unix+desc&start={}"

# Obtener total de productos desde la primera página
first_page_url = base_url.format(0)
response_first = requests.get(first_page_url, headers=headers)
if response_first.status_code == 200:
    soup_first = BeautifulSoup(response_first.text, "html.parser")
    subtitle_div = soup_first.find("div", class_="nd-ct__section-header-subtitle")
    if subtitle_div:
        # Ejemplo de texto: "1 - 48 de 656 productos"
        match = re.search(r'de\s+(\d+)', subtitle_div.text)
        if match:
            total_products = int(match.group(1))
        else:
            total_products = 0
    else:
        total_products = 0
else:
    print("Error al acceder a la primera página.")
    total_products = 0

if total_products == 0:
    print("No se pudo determinar el total de productos. Usando valor por defecto (656).")
    total_products = 656

products_per_page = 48

print(f"Total de productos: {total_products}")

# Lista para almacenar todos los enlaces de productos
product_links = []

# Recorrer todas las páginas y obtener los enlaces de productos
for start in range(0, total_products, products_per_page):
    page_url = base_url.format(start)
    response = requests.get(page_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            if "/pe/producto/" in a_tag["href"]:
                full_url = "https://platanitos.com" + a_tag["href"]
                product_links.append(full_url)
    else:
        print(f"Error al acceder a la página {page_url} (Status: {response.status_code})")
    time.sleep(1)  # Pausa para no saturar el servidor

# Eliminar duplicados
product_links = list(set(product_links))
print(f"Total de enlaces obtenidos: {len(product_links)}")

# Función para extraer los detalles de cada producto
def extract_product_details(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraer nombre del producto (<h1>)
            nombre_elem = soup.find("h1")
            nombre = nombre_elem.text.strip() if nombre_elem else None
            
            # Extraer precio (<div class="text-left">)
            precio_elem = soup.find("div", class_="text-left")
            precio = precio_elem.text.strip() if precio_elem else None
            
            # Extraer porcentaje de descuento (<span class="badge bg-primary badge-percentage">)
            descuento_elem = soup.find("span", class_="badge bg-primary badge-percentage")
            descuento = descuento_elem.text.strip() if descuento_elem else None
            
            # Extraer modelo: buscar el <span> que contiene "MPN:" y obtener el siguiente nodo de texto
            mpn_span = soup.find("span", text=lambda t: t and "MPN:" in t)
            modelo = None
            if mpn_span and mpn_span.next_sibling:
                modelo = mpn_span.next_sibling.strip()
            
            return {
                "URL": url,
                "Nombre": nombre,
                "Precio": precio,
                "Descuento": descuento,
                "Modelo": modelo
            }
        else:
            print(f"Error al acceder a {url} (Status: {response.status_code})")
            return {"URL": url, "Nombre": None, "Precio": None, "Descuento": None, "Modelo": None}
    except Exception as e:
        print(f"Excepción al procesar {url}: {e}")
        return {"URL": url, "Nombre": None, "Precio": None, "Descuento": None, "Modelo": None}

# Extraer detalles de productos usando multithreading para mejorar el tiempo de ejecución
product_details = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(extract_product_details, product_links))
    product_details.extend(results)

# Guardar los detalles en un archivo Excel con la fecha y hora actual
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"Detalles_Productos_{timestamp}.xlsx"
df = pd.DataFrame(product_details)
df.to_excel(filename, index=False, engine='openpyxl')

print(f"Archivo guardado: {filename}")
