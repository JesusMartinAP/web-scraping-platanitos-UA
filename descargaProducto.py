import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

# URL base de la página de productos
base_url = "https://platanitos.com/pe/productos?filter_brand[]=Under+Armour&sort=timestamp_active_unix+desc&start={}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Configuración de paginación
total_products = 656  # Total de productos según la web
products_per_page = 48

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
        print(f"Error al acceder a la página {page_url}")
    time.sleep(1)  # Pausa para no saturar el servidor

# Eliminar duplicados
product_links = list(set(product_links))
print(f"Total de enlaces obtenidos: {len(product_links)}")

# Lista para almacenar los detalles de cada producto
product_details = []

def extract_product_details(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraer nombre del producto (primer <h1>)
            nombre_elem = soup.find("h1")
            nombre = nombre_elem.text.strip() if nombre_elem else None
            
            # Extraer precio (primer <div class="text-left">)
            precio_elem = soup.find("div", class_="text-left")
            precio = precio_elem.text.strip() if precio_elem else None
            
            # Extraer porcentaje de descuento (<span class="badge bg-primary badge-percentage">)
            descuento_elem = soup.find("span", class_="badge bg-primary badge-percentage")
            descuento = descuento_elem.text.strip() if descuento_elem else None
            
            # Extraer modelo buscando un div que contenga "MPN:"
            modelo = None
            mpn_div = soup.find(lambda tag: tag.name == "div" and "MPN:" in tag.text)
            if mpn_div:
                modelo = mpn_div.text.replace("MPN:", "").strip()
            
            return {
                "URL": url,
                "Nombre": nombre,
                "Precio": precio,
                "Descuento": descuento,
                "Modelo": modelo
            }
        else:
            print(f"Error al acceder a {url} (Status code: {response.status_code})")
            return {
                "URL": url,
                "Nombre": None,
                "Precio": None,
                "Descuento": None,
                "Modelo": None
            }
    except Exception as e:
        print(f"Excepción al procesar {url}: {e}")
        return {
            "URL": url,
            "Nombre": None,
            "Precio": None,
            "Descuento": None,
            "Modelo": None
        }

# Visitar cada enlace y extraer la información del producto
for idx, link in enumerate(product_links, start=1):
    print(f"Extrayendo producto {idx} de {len(product_links)}")
    details = extract_product_details(link)
    product_details.append(details)
    time.sleep(1)  # Pausa entre solicitudes

# Guardar los detalles en un archivo Excel con la fecha y hora actual
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"Detalles_Productos_{timestamp}.xlsx"
df = pd.DataFrame(product_details)
# Especifica el engine para asegurarnos que se use openpyxl
df.to_excel(filename, index=False, engine='openpyxl')

print(f"Archivo guardado: {filename}")
