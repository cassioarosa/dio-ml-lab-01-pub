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


def scrape_images(
    query: str,
    num_images: int = 5,
    main_folder: str = "Dataset",
    on_save: Callable[[str], None] | None = None,
    variations: List[str] = [],
) -> None:

    query_folder = os.path.join(main_folder, query.replace(" ", "_"))
    # Criando o diretório para salvar as imagens (se não existir)
    if not os.path.exists(query_folder):
        os.makedirs(query_folder)

    def initialize_webdriver(retries: int = 3) -> WebDriver:
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
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

    # Inicializando o WebDriver com tratamento de exceção
    driver = initialize_webdriver()

    def cleanup_webdriver(driver: WebDriver) -> None:
        driver.quit()

    def take_screenshot() -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"issue_{timestamp}.png")

    def save_image_clipboard(url: str, img_local_path: str) -> None:
        try:

            # Abre uma nova aba
            driver.switch_to.new_window('tab')
            # Para navegar para uma URL específica
            driver.get(url)

            # take the screenshot of the image
            element = driver.find_element(By.TAG_NAME, "img")
            element.screenshot(img_local_path)
            print(f"Imagem salva em {img_local_path}")

            if on_save is not None:
                on_save(img_local_path)

        except Exception as e:
            print(f"Erro ao salvar imagem: {e}")
            take_screenshot()
            raise
        finally:
            ## Close all tabs except the main one
            for handle in driver.window_handles[1:]:
                driver.switch_to.window(handle)
                driver.close()

            driver.switch_to.window(driver.window_handles[0])

    count: int = 0

    # Função para buscar as imagens no Google
    def download_google_images(web_query: str) -> None:

        nonlocal count
        # URL de pesquisa do Google (com query string tbs=isz:l para imagens grandes)
        search_url = (
            f"https://www.google.com/search?hl=pt-BR&tbm=isch&q={web_query}&tbs=isz:l"
        )
        driver.get(search_url)
        time.sleep(0.5)  # Esperando a página carregar

        def get_all_images() -> List[WebElement]:
            return driver.find_elements(By.CSS_SELECTOR, "div#search h3 img")

        # Encontrando as imagens na página
        img_elements: List[WebElement] = get_all_images()

        actions = ActionChains(driver)

        def move_selection_to_image(img_element: WebElement) -> str:
            # ❗ href attribute of anchor is filled only after hovering over the image
            actions.move_to_element(img_element).perform()
            aElement = img_element.find_element(By.XPATH, "ancestor::a[1]")
            href = aElement.get_attribute("href")
            if href is None or href == "":
                raise ValueError("href is None or empty")
            return href

        def get_img_url(href: str) -> str:
            # Capture "imgurl" query string in a[href]
            my_dict: Dict[str, str] = {}
            for item in href.split("&"):
                (key, value) = item.split("=")
                my_dict[key] = unquote(value)  # remove URL encoding
            if "imgurl" not in my_dict:
                raise ValueError("imgurl not found in my_dict")
            return my_dict["imgurl"]

        while count < num_images:
            for img_element in img_elements:  # type WebElement

                digits: int = len(str(num_images))
                count_name: str = str(count + 1).zfill(digits)
                print(f"Processando imagem {count_name} {web_query}")

                if count >= num_images:
                    print(
                        f"Processamento de `{web_query}` concluído com {count} imagens."
                    )
                    return

                try:
                    href = move_selection_to_image(img_element)
                    img_url = get_img_url(href)

                    if img_url:
                        img_local_path = os.path.join(
                            query_folder, f"image_{count_name}.png"
                        )
                        save_image_clipboard(img_url, img_local_path)
                        count += 1
                    else:
                        raise ValueError("img_url is None or empty")
                except Exception as e:
                    print(f"Erro ao baixar imagem: {e}")

                    continue

            # Next Page
            body = driver.find_element(By.CSS_SELECTOR, "body")  # Select body element
            if not body:
                print(f"Body element not found for {web_query}")
                break

            body.send_keys(Keys.PAGE_DOWN)  # Envia a tecla Page Down
            time.sleep(1)  # aguardar imagens carregarem

            all_elements = get_all_images()
            last_element_index = all_elements.index(img_elements[-1]) + 1
            img_elements = all_elements[last_element_index:]

            if len(img_elements) == 0:
                print(f"End of pagination for {web_query}")
                break

    try:

        for variation in ["", *variations]:
            web_query = f"{query} {variation}".strip()
            download_google_images(web_query)

            if count >= num_images:
                break

        if count < num_images:
            print(
                f'Processamento de `{query}` concluído "Parcialmente" com {count} imagens.'
            )
        else:
            print(
                f'Processamento de `{query}` concluído com "Todas" imagens solicitadas.'
            )
    except Exception as e:
        print(f"Erro ao executar downdload_google_images: {e}")
        take_screenshot()
    finally:
        cleanup_webdriver(driver)