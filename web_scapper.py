import os
import time
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from typing import Callable, List, Dict
from datetime import datetime

def scrape_images(query: str, num_images: int = 5, main_folder: str = "Dataset", on_save: Callable[[str], None] | None = None ) -> None:
    def initialize_webdriver(retries: int = 3) -> WebDriver:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        for attempt in range(retries):
            try:
                return webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=options,
                )
            except Exception as e:
                print(
                    f"Erro ao inicializar o WebDriver (tentativa {attempt + 1} de {retries}): {e}"
                )
                if attempt == retries - 1:
                    raise
                time.sleep(2)
        raise RuntimeError("Falha ao inicializar o WebDriver após várias tentativas")

    def cleanup_webdriver(driver: WebDriver) -> None:
        driver.quit()

    # Inicializando o WebDriver com tratamento de exceção
    driver = initialize_webdriver()

    def take_screenshot() -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"issue_{timestamp}.png")

    def save_image_clipboard(url: str, full_path: str) -> None:
        try:
            # open a new tab
            driver.execute_script(f"window.open('{url}');")
            driver.switch_to.window(driver.window_handles[-1])

            # take the screenshot of the image
            element = driver.find_element(By.TAG_NAME, "img")
            element.screenshot(full_path)
            print(f"Imagem salva em {full_path}")

            if on_save is not None:
                on_save(full_path)

            # close the tab and switch back to the main tab
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])
        except Exception as e:
            print(f"Erro ao salvar imagem: {e}")
            take_screenshot()

            # leave only the first tab opened
            while len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])

            raise

    # Função para buscar as imagens no Google
    def download_google_images() -> None:
        query_folder = os.path.join(main_folder, query.replace(" ", "_"))

        # Criando o diretório para salvar as imagens (se não existir)
        if not os.path.exists(query_folder):
            os.makedirs(query_folder)

        # URL de pesquisa do Google (com query string tbs=isz:l para imagens grandes)
        search_url = (
            f"https://www.google.com/search?hl=pt-BR&tbm=isch&q={query}&tbs=isz:l"
        )
        driver.get(search_url)
        time.sleep(0.5)  # Esperando a página carregar

        def get_all_images() -> List[WebElement]:
            return driver.find_elements(By.CSS_SELECTOR, "div#search h3 img")

        # Encontrando as imagens na página
        img_elements: List[WebElement] = get_all_images()
        count: int = 0
        actions = ActionChains(driver)

        while count < num_images:
            for img_element in img_elements:  # type WebElement
                print(f"Processando imagem {count}")
                if count >= num_images:
                    break
                try:
                    # ❗ href attribute of anchor is filled only after hovering over the image
                    actions.move_to_element(img_element).perform()
                    aElement = img_element.find_element(By.XPATH, "ancestor::a[1]")
                    href = aElement.get_attribute("href")
                    if href is None or href == "":
                        raise ValueError("href is None or empty")

                    # Capture "imgurl" query string in a[href]
                    my_dict: Dict[str, str] = {}
                    for item in href.split("&"):
                        (key, value) = item.split("=")
                        my_dict[key] = unquote(value)  # remove URL encoding
                    if "imgurl" not in my_dict:
                        raise ValueError("imgurl not found in my_dict")

                    if img_url := my_dict["imgurl"]:
                        img_full_path = os.path.join(
                            query_folder, f"image_{count + 1}.png"
                        )
                        save_image_clipboard(img_url, img_full_path)
                        count += 1
                    else:
                        raise ValueError("img_url is None or empty")
                except Exception as e:
                    print(f"Erro ao baixar imagem: {e}")
                    continue

            # Next Page
            body = driver.find_element(By.CSS_SELECTOR, "body")  # Select body element
            body.send_keys(Keys.PAGE_DOWN)  # Envia a tecla Page Down
            time.sleep(1)  # aguardar imagens carregarem

            all_elements = get_all_images()
            last_element_index = all_elements.index(img_elements[-1])
            img_elements = all_elements[last_element_index:]

    try:
        download_google_images()
        print(f"Processamento de `{query}` concluído.")
    finally:
        cleanup_webdriver(driver)

