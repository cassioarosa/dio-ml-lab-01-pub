Olá, saudações!

O proteto está desenvolvimento seguindo 3 tópicos:

- Web Scrapping das imagens utilizando Selenium com Google Chrome Headless.
- Treinamento do Modelo utilizando **Transfer Learning**.
- Teste do Modelo com Upload de imagens

A execução do projeto  pode ser feita de forma sequêncial, célula a célula à partir do arquivo [notebook.ipynb](notebook.ipynb).

## Imagem

Para simplificar o acompanhamento de uma execução de demostração preparamos o GIF abaixo.

## Pré-requisitos

Projeto foi desenvolvido em WSL2. Instalar Google Chrome. _Rodar Manualmente em WSL_.

``` bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable
```

Instalar depenências utilizando `-venv`.

``` bash
# configura ambiente virtual
python3 -m venv venv

# ativa ambiente virtual
source venv/bin/activate

# instalar dependências 
pip install -r requirements.txt
```
