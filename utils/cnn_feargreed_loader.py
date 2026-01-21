import json
import requests
import datetime
from pathlib import Path
from typing import Optional, Union
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"
CACHE_FILE = Path("data/feargreed.json")
URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

class FearGreedRecord:
    def __init__(self, value: int, description: str, date: datetime.date):
        self.value = value
        self.description = description
        self.date = date

class DateOutOfRangeError(Exception):
    """Excepción lanzada cuando la fecha solicitada está fuera del rango de datos disponibles."""
    pass

def load_data(force_refresh=False) -> dict:
    """Descarga o carga desde cache el JSON completo del endpoint CNN."""
    if CACHE_FILE.exists() and not force_refresh:
        mtime = datetime.date.fromtimestamp(CACHE_FILE.stat().st_mtime)
        if mtime == datetime.date.today():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        # Si el archivo existe pero no es de hoy, se descargará de nuevo
    
    # Headers para simular un navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://money.cnn.com/data/fear-and-greed/",
        "Origin": "https://money.cnn.com",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }
    
    try:
        resp = requests.get(URL, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "fear_and_greed_historical" in data and "data" in data["fear_and_greed_historical"]:
            transformed_records = []
            for rec in data["fear_and_greed_historical"]["data"]:
                dt_obj = datetime.datetime.fromtimestamp(rec["x"] / 1000, datetime.UTC)
                date_str = dt_obj.strftime("%Y-%m-%d")      # Formato YYYY-MM-DD

                # Crear el nuevo registro con lo campos solicitados
                transformed_rec = {
                   "timestamp_ms": rec["x"],                # Tiempo original en milisegundos
                   "value": float(rec["y"]),                # Valor del Fear Greed
                   "description": rec.get("rating", ""),    # Descripción -> Fear, Neutral, Greed
                   "date": date_str
                }
                transformed_records.append(transformed_rec)
            # Preparar los datos transformados para guardar
            transformed_data = {
                "fear_and_greed_historical": {
                    "data": transformed_records
                }
            }
        else:
            # Manejar el caso donde la estructura esperada no esta presente
            logger.warning(f"Advertencia: La estructura de datos esperada no se encontró en la respuesta.")
            # return data
            ValueError(f"Estructura de datos JSON no soportada.")

        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(transformed_data, f)          # Se guarda el JSON transformado
        return transformed_data                     # Retorna los datos transformados
    except Exception as e:
        # Si falla la descarga pero existe el caché, usamos el caché
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                try:
                    cached_data = json.load(f)
                    # Verificar si la cache tiene el formato transformado
                    if "fear_and_greed_historical" in cached_data and \
                        len(cached_data["fear_and_greed_historical"].get("data", [])) > 0 and \
                        "date" in cached_data["fear_and_greed_historical"]["data"][0]:
                        return cached_data
                    else:
                        logger.warning(f"El cache {CACHE_FILE} tiene un formato antiguo. Se requiere descargar nuevamente.")
                        return None
                except json.JSONDecodeError:
                    logger.warning(f"El archivo {CACHE_FILE} no es un archivo JSON valido.")
                    return None
        # Si no hay archivo JSON ni cache
        logger.warning(f"Error crítico al obtener o transformar datos de CNN Fear & Greed: {str(e)}")
        return None

def get_value_by_date(target_date: Union[datetime.date, str]) -> Optional[FearGreedRecord]:
    """Devuelve un objeto FearGreedRecord con valor, descripción y fecha."""
    try:
        # Convertir a objeto date si es una cadena
        if isinstance(target_date, str):
            target_date_obj = datetime.datetime.strptime(target_date, DATE_FORMAT).date()
        elif isinstance(target_date, datetime.date):
            target_date_obj = target_date
        else:
            raise TypeError("La fecha debe ser un objeto date o una cadena en formato 'YYYY-MM-DD'")
        
        data = load_data()
        if data is None:
            return None
            
        records = data["fear_and_greed_historical"]["data"]
        # - Validación de rango de fechas - #

        if not records:
            # Si no hay registros se lanza un error
            raise DateOutOfRangeError("No hay datos disponibles en el archivo cache")
        # Obtener la primera y ultima fila del conjunto de datos
        first_date_str = records[0]["date"]
        last_date_str = records[-1]["date"]
        
        first_date = datetime.datetime.strptime(first_date_str, DATE_FORMAT).date()
        last_date = datetime.datetime.strptime(last_date_str, DATE_FORMAT).date()

        # Verificar si la fecha objetivo esta fuera del rango
        if target_date_obj < first_date or target_date_obj > last_date:
            raise DateOutOfRangeError(f"La fecha solicitada ({target_date_obj}) esta fuera del rango de datos disponibles ({first_date} a {last_date})")
        
        # Buscar la fila que coincide con la fecha
        for rec in records:
            rec_date_str = rec["date"]              # Obtener la fecha transformada del JSON
            rec_date = datetime.datetime.strptime(rec_date_str, DATE_FORMAT).date()
            if rec_date == target_date_obj:
                return FearGreedRecord(
                    value=int(rec["value"]),
                    description=rec["description"],
                    date=rec_date
                )
        
        raise DateOutOfRangeError(f"No se encontraron datos exactos para la fecha solicitada ({target_date_obj}) dentro del rango disponible ({first_date} a {last_date}).")

    except DateOutOfRangeError:
        # Relanzar la excepción específica para que el llamador la maneje
        raise
    except Exception as e:
        print(f"Error al obtener valor por fecha: {e}")
        return None