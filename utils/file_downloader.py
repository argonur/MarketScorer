import os
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from data.market_dates import get_last_trading_date
import hashlib

def _calculate_file_hash(filepath: str) -> str:
    """Calcula el hash MD5 de un archivo."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def _save_hash(filepath: str, file_hash: str):
    """Guarda el hash en un archivo .hash."""
    hash_filepath = filepath + ".hash"
    with open(hash_filepath, 'w') as f:
        f.write(file_hash)

def _load_hash(filepath: str) -> str | None:
    """Carga el hash desde un archivo .hash."""
    hash_filepath = filepath + ".hash"
    if not Path(hash_filepath).exists():
        return None
    with open(hash_filepath, 'r') as f:
        return f.read().strip()

def download_latest_file(
    base_url: str,
    file_name: str,
    save_dir: str,
    pattern: str = None
) -> str | None:
    try:
        # Obtener la última fecha de cierre del mercado
        last_trading_date = get_last_trading_date()
        today_str = last_trading_date.strftime("%Y-%m-%d")

        # Nombre base y extensión
        name_base = file_name.rsplit('.', 1)[0]
        extension = file_name.split('.')[-1]

        # Nombre del archivo actual (con fecha)
        current_filename = f"{name_base}_{today_str}.{extension}"
        current_filepath = Path(save_dir) / current_filename

        # Generar patrón si no se proporcionó
        if pattern is None:
            pattern = f"{name_base}_*.xls"

        # Buscar archivos existentes
        existing_files = list(Path(save_dir).glob(pattern))

        # Si hay archivos, encontrar el más reciente
        if existing_files:
            latest_file = None
            latest_date = None

            for file in existing_files:
                try:
                    date_str = file.stem.split('_')[-1]
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    if latest_date is None or file_date > latest_date:
                        latest_date = file_date
                        latest_file = file

                except ValueError:
                    continue  # Ignorar archivos con formato incorrecto

            # Si el archivo más reciente es del último cierre del mercado, verificar si el contenido ha cambiado
            if latest_date == last_trading_date:
                print(f"✅ Archivo más reciente ya existe: {latest_file.name}")

                # Calcular hash del archivo existente
                existing_hash = _calculate_file_hash(str(latest_file))
                #print(f"🔍 Hash del archivo existente: {existing_hash}")

                # Obtener la URL real del archivo
                download_url = _get_download_url(base_url)
                if not download_url:
                    print("❌ No se pudo obtener la URL de descarga.")
                    return str(latest_file)  # Devolver el archivo existente

                # Descargar el archivo temporalmente para calcular su hash
                #print(f"⏳ Descargando archivo temporal para comparar hash...")
                #print(f"⏳ Comprobando...")
                temp_filepath = current_filepath.with_suffix(".tmp")
                try:
                    respuesta = requests.get(download_url)
                    if respuesta.status_code != 200:
                        raise Exception(f"Error al descargar: {respuesta.status_code}")

                    with open(temp_filepath, 'wb') as archivo:
                        archivo.write(respuesta.content)

                    # Calcular hash del archivo descargado
                    new_hash = _calculate_file_hash(str(temp_filepath))
                    #print(f"🔍 Hash del archivo nuevo: {new_hash}")

                    # Comparar hashes
                    if existing_hash == new_hash:
                    #    print("✅ El archivo no ha cambiado. No se descarga nuevamente.")
                        temp_filepath.unlink()  # Eliminar archivo temporal
                        return str(latest_file)
                    else:
                        print("🔄 El archivo ha cambiado. Descargando nuevo...")
                        # Reemplazar el archivo existente con el nuevo
                        temp_filepath.replace(current_filepath)
                        _save_hash(str(current_filepath), new_hash)
                        print(f"✅ Archivo actualizado: {current_filepath}")
                        return str(current_filepath)

                except Exception as e:
                    print(f"❌ Error al comparar hashes: {e}")
                    temp_filepath.unlink(missing_ok=True)  # Asegurar limpieza
                    return str(latest_file)  # Devolver el archivo existente

            print(f"🔄 Archivo más reciente ({latest_file.name}) es anterior al último cierre. Descargando nuevo...")

        # Obtener la URL real del archivo
        download_url = _get_download_url(base_url)
        if not download_url:
            print("❌ No se pudo obtener la URL de descarga.")
            return None

        # Descargar nuevo archivo
        #print(f"⏳ Descargando nuevo archivo: {current_filename} desde {download_url}")
        print(f"⏳ Descargando nuevo archivo: {current_filename}")
        try:
            respuesta = requests.get(download_url)
            if respuesta.status_code == 200:
                os.makedirs(save_dir, exist_ok=True)
                with open(current_filepath, 'wb') as archivo:
                    archivo.write(respuesta.content)
                print(f"✅ Archivo guardado en: {current_filepath}")

                # Guardar hash
                file_hash = _calculate_file_hash(str(current_filepath))
                _save_hash(str(current_filepath), file_hash)
                print(f"🔒 Hash guardado: {file_hash}")

                return str(current_filepath)
            else:
                raise Exception(f"Error al descargar: {respuesta.status_code}")
        except Exception as e:
            print(f"❌ Error al descargar el archivo: {e}")
            return None

    except Exception as e:
        print(f"❌ Error en download_latest_file: {e}")
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