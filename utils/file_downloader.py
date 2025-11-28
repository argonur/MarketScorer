import os
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from data.market_dates import get_last_trading_date
import hashlib

def download_latest_file(base_url: str, file_name: str, save_dir: str) -> str | None:
    try:
        download_url = _get_download_url(base_url)
        if not download_url:
            print(f"❌ No se pudo obtener la URL de descarga.")
            return None

        # Construir la ruta completa del archivo
        filepath = Path(save_dir) / "latest.xls"
        os.makedirs(save_dir, exist_ok=True)

        # Descargar el archivo
        print(f"⏳ Descargando el archivo.....")
        respuesta = requests.get(download_url)
        if respuesta.status_code != 200:
            raise Exception(f"Error al descargar: {respuesta.status_code}")

        with open(filepath, 'wb') as archivo:
            archivo.write(respuesta.content)

        print(f"✅ Archivo guardado en: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Error al descargar el archivo: {e}")
        return None

def _get_download_url(base_url: str) -> str | None:
    try:
        respuesta = requests.get(base_url)
        if respuesta.status_code != 200:
            raise Exception(f"Error al cargar la página: {respuesta.status_code}")

        sopa = BeautifulSoup(respuesta.content, 'html.parser')
        boton = sopa.find('a', {'data-aid': 'DOWNLOAD_DOCUMENT_LINK_RENDERED'})

        if not boton or not boton.get('href'):
            raise Exception("No se encontró el botón de descarga o no tiene href")

        # Convertir URL relativa a absoluta
        download_url = urljoin(base_url, boton['href'])
        return download_url

    except Exception as e:
        print(f"❌ Error al obtener la URL de descarga: {e}")
        return None