from indicators.IndicatorModule import IndicatorModule
from utils.file_downloader import download_latest_file
from data.market_dates import yfinance_window_for_last_close
from dotenv import load_dotenv
import yfinance as yf
import os
import pandas as pd
import logging

load_dotenv()
URL = os.getenv("SHILLER_PE_URL")
NAME = "latest.xls"
PATH_DIR = os.getenv("SAVE_PATH", "data/inputs")
MAX_VALUE = 120
start_date, end_date = yfinance_window_for_last_close()
SYMBOL = "^SPX"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShillerPEIndicator(IndicatorModule):
    #Constructor
    def __init__(self):
        super().__init__()
        self.cape_average = None # Para almacenar el promedio calculado
        self.daily_cape = None
        self.url = URL
        self.last_close = None
        self.promedio_cape_30 = None
        self.desv_cape_30 = None

    def fetch_data(self, date):
            logger.info(f" -> Fecha a usar: {date}")
            # Descargar el archivo mas reciente
            filepath = download_latest_file(base_url=URL, file_name=NAME, save_dir=PATH_DIR)
            if not filepath:
                raise RuntimeError("No se pudo descargar el archivo Shiller PE")

            # print(f"[Shiller]: Fecha a usar: {date}")
            # Proximamente los metodos 'process' deberán aceptar date para buscar por fecha
            self._process_data(filepath)
            self._process_data_30(filepath)

            # Obtener el ultimo cierre de S&P 500
            last_close_spx = self.get_last_close(SYMBOL, date)
            if last_close_spx is None or self.cape_average is None:
                raise RuntimeError("Datos insuficientes para calcular CAPE diario")

            self.daily_cape = round(last_close_spx / self.cape_average, 2)
            return self.daily_cape

    def normalize(self, date):
        if self.daily_cape is None or self.promedio_cape_30 is None or self.desv_cape_30 is None:
            raise RuntimeError("No se puede normalizar: faltan datos criticos")

        if self.desv_cape_30 <= 0.1:
            return 1.0   # salir inmediatamente, no recalcular

        z = (self.daily_cape - self.promedio_cape_30) / self.desv_cape_30
        score = max(0, min(100, 100 - max(0, z) * 25)) / 100
        return score

    def get_score(self, date):
        if self.daily_cape is None or self.promedio_cape_30 is None or self.desv_cape_30 is None:
            self.fetch_data(date)
        value = self.normalize(date)
        return round(value, 2)
    
    def _process_data(self, file_path):
        try:
            # Detectar extensión y elegir engine
            ext = str(file_path).split(".")[-1].lower()
            engine = "xlrd" if ext == "xls" else "openpyxl"
            # Leer el archivo
            df = pd.read_excel(file_path, sheet_name="Data", engine=engine)
            # Leer la columna correspondiente
            columna_10 = df.iloc[:, 10]
            # Conersión y limpiesa de datos
            columna_numerica = pd.to_numeric(columna_10, errors="coerce")
            columna_limpia = columna_numerica.dropna()
            # Obtener las ultimas X filas
            val_obtenidos = columna_limpia.tail(MAX_VALUE)
            # Se verifica que si haya datos suficientes
            if len(val_obtenidos) < MAX_VALUE:
                print(f"⚠️ Solo se encontraron {len(val_obtenidos)} valores válidos (se necesitan {MAX_VALUE}).")

            if val_obtenidos.empty:
                raise RuntimeError("Archivo Shiller PE no contiene datos válidos en la columna esperada")
            
            # Calcular promedio
            self.cape_average = val_obtenidos.mean()   # Guardar el promedio en el atributo de clases
        except Exception as e:
            raise RuntimeError(f"Error al procesar el archivo {file_path}: {e}")
    
    def _process_data_30(self, file_path):
        ext = str(file_path).split(".")[-1].lower()
        engine = "xlrd" if ext == "xls" else "openpyxl"
        df = pd.read_excel(file_path, sheet_name="Data", engine=engine)
        columna_12 = pd.to_numeric(df.iloc[:, 12], errors="coerce").dropna()
        val_obtenidos = columna_12.tail(360)

        if len(val_obtenidos) < 360:
            print(f"⚠️ Solo {len(val_obtenidos)} valores válidos (se necesitan 360)")
        
        if val_obtenidos.empty:
            raise RuntimeError("Archivo Shiller PE no contiene datos válidos en la columna esperada")

        self.promedio_cape_30 = val_obtenidos.mean() if not val_obtenidos.empty else None
        self.desv_cape_30 = val_obtenidos.std() if not val_obtenidos.empty else None

    def get_last_close(self, symbol, date):
        sp500 = yf.Ticker(symbol)
        logging.info(f"[Shiller]: Fecha para last_close: {date}")
        data = sp500.history(start=start_date, end=end_date, auto_adjust=True)
        if data.empty:
            print("❌ No se pudieron obtener datos del índice S&P 500")
            return None
        return float(data['Close'].iloc[0])

if __name__ == "__main__":
    try:
        indicator = ShillerPEIndicator()
        indicator.fetch_data()
        print(f"Promedio de los 10 años de Real Earnings: {indicator.cape_average}")
        print(f"El CAPE diario es: {indicator.daily_cape}")
        print("Ultimo cierre de S&P 500:", indicator.last_close)
        print(f"Promedio de CAPE 30: {indicator.promedio_cape_30}")
        print(f"Desviación estandar CAPE 30: {indicator.desv_cape_30}")
        print(f"Score final: {indicator.get_score()}")

    except Exception as e:
        print(f"Error critico en ShillerPEIndicator: {e}")