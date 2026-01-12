import json
import os
from datetime import date, datetime
from typing import Dict, Any, Optional
from data.market_dates import get_last_trading_close

class MarketReport:
    """ Clase para generar y gestionar los resultados del sistema en cache persistente. """
    def __init__(self, filepath: str = "data/market_report.json"):
        self.filepath = filepath
        self.data = {}
        self.load() # Cargar datos existentes al inicializar

    def set_data(self, key: str, vale: Any, date_str: str = None):
        """ Almacena un dato con su fecha de calculo.  """
        if date_str is None:
            date_str = get_last_trading_close().date()
            if date_str is None:
                date_str = datetime.now().date()
        if key not in self.data:
            self.data[key] = {}

        self.data[key]["value"] = vale
        self.data[key]["date"] = date_str

        self.save()

    def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        """ Obtener un dato por clave """
        return self.data.get(key)
    
    def set_indicator_data(self, indicator_name: str, data: Dict[str, Any], calc_date: str):
        """ Almacenar todos los datos de indicador especifico """
        if indicator_name not in self.data:
            self.data[indicator_name] = {}
        self.data[indicator_name]["calc_date"] = calc_date
        self.data[indicator_name]["timestamp"] = datetime.now().isoformat()
        self.data[indicator_name].update(data) # Actualizar con los nuevos datos
        self.save()
    
    def get_indicator_data(self, indicator_name: str) -> Optional[Dict[str, Any]]:
        """ Obtener todos los datos de un indicador por su nombre """
        return self.data.get(indicator_name)
    
    def get_all_data(self) -> Dict[str, Any]:
        """ Obtener todos los datos almacenados """
        return self.data.copy()
    
    def save(self):
        """ Guardar los datos en un archivo JSON """
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w' , encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def load(self):
        """ Cargar todos los datos de un archivo """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}
        except json.JSONDecodeError:
            self.data = {}
            print(f"⚠️ Archivo de reporte corrupto, reiniciando.....")

    def clear(self):
        """ Limpiar todos los datos """
        self.data = {}
        self.save()

    def is_up_to_date(self, indicator_name: str, max_age_days: int = 1) -> bool:
        """Verifica si los datos del indicador están actualizados."""
        data = self.get_indicator_data(indicator_name)
        if not data or "calc_date" not in data:
            return False

        try:
            from datetime import datetime, timedelta
            data_date = datetime.fromisoformat(data["calc_date"])
            today = datetime.now()
            return (today - data_date).days <= max_age_days
        except Exception:
            return False