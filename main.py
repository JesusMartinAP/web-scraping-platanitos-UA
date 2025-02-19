import flet as ft
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de logging
logging.basicConfig(level=logging.INFO)

def main(page: ft.Page):
    page.title = "Web Scraper Platanitos"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    progress_bar = ft.ProgressBar(width=400, visible=False)
    status_text = ft.Text("", color=ft.colors.GREY_600)
    result_text = ft.Text("", color=ft.colors.GREEN_800)

    def start_scraping(e):
        progress_bar.visible = True
        status_text.value = "Iniciando scraping..."
        result_text.value = ""
        page.update()
        try:
            # Configurar opciones de Chrome
            options = webdriver.ChromeOptions()
            # Para ver la ejecución, descomenta la siguiente línea (sin headless)
            # options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=9222")

            # Inicializar el servicio usando webdriver_manager (descarga el driver automáticamente)
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            # URL principal a scrapear
            url = "https://platanitos.com/pe/productos?filter_brand[]=Under+Armour&sort=timestamp_active_unix+desc"
            driver.get(url)

            # Esperar a que se cargue el listado de productos
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "productoItem"))
            )

            # Encontrar todos los elementos que representan un producto
            product_cards = driver.find_elements(By.CLASS_NAME, "productoItem")
            if not product_cards:
                result_text.value = "No se encontraron productos en la página."
                result_text.color = ft.colors.RED_800
                page.update()
                driver.quit()
                return

            total_products = len(product_cards)
            productos = []
            errors = []

            for index, card in enumerate(product_cards):
                try:
                    # Obtener el enlace del producto
                    product_link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Abrir el producto en una nueva pestaña
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(product_link)

                    # Esperar a que se cargue el título (elemento <h1>) del producto
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "h1"))
                    )

                    # Extraer la información indicada:
                    marca = driver.find_element(By.CSS_SELECTOR, 'a[href*="/marca/"]').text.strip()
                    nombre = driver.find_element(By.TAG_NAME, "h1").text.strip()
                    # Se extrae el modelo a partir de un elemento que contenga "MPN:"; se espera que el texto tenga el formato "MPN: <valor>"
                    modelo_text = driver.find_element(By.XPATH, '//div[contains(text(), "MPN:")]').text
                    modelo = modelo_text.split("MPN:")[-1].strip()
                    descripcion = driver.find_element(By.ID, "description").text.strip()

                    # Agregar los datos del producto a la lista
                    productos.append({
                        'Marca': marca,
                        'Nombre': nombre,
                        'Modelo': modelo,
                        'Descripción': descripcion,
                        'URL': product_link
                    })

                    # Cerrar la pestaña del producto y volver a la principal
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    # Actualizar barra de progreso y estado
                    progress_bar.value = (index + 1) / total_products
                    status_text.value = f"Procesando {index + 1}/{total_products} productos..."
                    page.update()

                except Exception as err:
                    errors.append(f"Error en producto {index + 1}: {str(err)}")
                    logging.error(str(err))
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    continue

            # Guardar los datos extraídos en un archivo Excel
            if productos:
                df = pd.DataFrame(productos)
                df.to_excel("productos_platanitos.xlsx", index=False)
                result_text.value = f"¡Scraping completado! {len(productos)} productos guardados. Errores: {len(errors)}"
                if errors:
                    result_text.value += "\nErrores:\n" + "\n".join(errors)
                    result_text.color = ft.colors.RED_800
            else:
                result_text.value = "No se encontraron productos válidos."
                result_text.color = ft.colors.RED_800

            driver.quit()
            progress_bar.visible = False
            status_text.value = ""
            page.update()

        except Exception as e:
            result_text.value = f"Error general: {str(e)}"
            result_text.color = ft.colors.RED_800
            page.update()
            logging.error(str(e))

    # Configuración de la interfaz con Flet
    page.add(
        ft.Column([
            ft.Icon(name=ft.icons.WEB_STORIES, size=50),
            ft.Text("Scraper Platanitos", size=24, weight="bold"),
            ft.ElevatedButton(
                "Iniciar Scraping",
                icon=ft.icons.DOWNLOAD,
                on_click=start_scraping
            ),
            progress_bar,
            status_text,
            result_text
        ], alignment="center", spacing=20)
    )

if __name__ == "__main__":
    ft.app(target=main)
