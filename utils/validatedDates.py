from datetime import datetime
import pandas_market_calendars as mcal
import data.market_dates as md
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

fecha = "2025-12-19"
format = "%Y-%m-%d"
LIMIT_UMBRAL = "1990-01-01"

logger.debug(f"Fecha de prueba: {fecha}")
def validate_date_iso_format(_date: str) -> bool:
  """Valida si una cadena coincide con un formato de fecha específico."""
  try:
    # Intenta convertir la cadena a un objeto datetime
    datetime.strptime(_date, format).date()
    return True # Si tiene éxito, la fecha es válida
  except ValueError as e:
    logger.warning(f"Invalid Date Type Format: {e}")
    return False # Si falla, el formato es incorrecto

def validate_date_not_future(_date: str) -> bool:
    try:
        today = md.get_market_today()
        fecha = datetime.strptime(_date, format).date()
        if fecha <= today:
            return True  # es válida, no futura
        else:
            raise ValueError(f"La fecha {_date} es futura o aún no cierra el mercado")
    except Exception as e:
        logger.warning(f"{e}")
        return False

def validate_date_in_range(_date: str) -> bool:
    try:
        fecha = datetime.strptime(_date, format).date()
        rango = datetime.strptime(LIMIT_UMBRAL, format).date()
        # Recibo 1995-01-01 que es una fecha menor que 1990-01-01
        if fecha > rango:
            return True
        else:
            raise ValueError(f"Fecha fuera del rango {rango}")
    except Exception as e:
        logger.warning(f"Date Out Of Range: {e}")
        return False

def validate_date_was_valid(_date: str) -> bool:
    nyse = mcal.get_calendar("NYSE")
    # fecha tiene un valor definido en 2025-12-17
    fecha = datetime.strptime(_date, format).date()
    # Consultar calendario oficial para esa fecha
    schedule = nyse.schedule(start_date=fecha.isoformat(), end_date=fecha.isoformat())
    return not schedule.empty

def get_a_validated_date(_date: str) -> bool:
    try:
        if not validate_date_iso_format(_date):
            raise ValueError(f"Formato inválido: {_date}")
        if not validate_date_not_future(_date):
            raise ValueError(f"Future Date Error: {_date}")
        if not validate_date_in_range(_date):
            raise ValueError(f"Date Out Of Range Error: {_date}")
        if not validate_date_was_valid(_date):
            raise ValueError(f"Invalid Market Day Error: {_date}")
        return True
    except Exception as e:
        logger.warning(f"Ocurrió un error crítico en la fecha solicitada -> {e}")
        return False

if __name__ == "__main__":
    try:
        logger.info(f"-------------------------------------------------")
        logger.debug(f"Estatus final de la fecha: {get_a_validated_date(fecha)}")
    except Exception as e:
        logger.warning(f"Ocurrio un error critico: {e}")