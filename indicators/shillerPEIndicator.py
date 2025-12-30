from indicators.IndicatorModule import IndicatorModule
from utils.file_downloader import download_latest_file
from data.market_dates import yfinance_window_for_last_close
from utils.MarketReport import MarketReport
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
        # Atributos para almacenar los resultados y la fecha de cálculo
        self._last_calculated_date = None
        self.cape_average = None
        self.daily_cape = None
        self.url = URL
        self.last_close = None
        self.promedio_cape_30 = None
        self.desv_cape_30 = None

    def _is_cached(self, date):
        # Verifica si los datos ya estan calculados para esta fecha
        return self._last_calculated_date == date and self.daily_cape is not None

    def fetch_data(self, date):
            # Comenzamos con la verificación en cache
            if self._is_cached(date):
                logger.info(f"[ShillerPE | FetchData] -> Datos ya calculados para {date}.... Usando la versión caché.")
                return self.daily_cape
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
            self.last_close = last_close_spx
            if last_close_spx is None or self.cape_average is None:
                raise RuntimeError("Datos insuficientes para calcular CAPE diario")

            self.daily_cape = round(last_close_spx / self.cape_average, 2)
            self._last_calculated_date = date # Marcar la fecha como calculada

            # Guardar en MarketReport
            self.set_report(date)
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
        # Primero, asegurarnos de que los datos estén calculados.
        if not self._is_cached(date):
            logger.info(f"[ShillerPE | GetScore]: Calculando datos para {date}...")
            self.fetch_data(date)

        # Ahora, normalizar los datos ya calculados.
        normalized_score = self.normalize(date)
        logger.info(f"Refactorización de Shiller -> {round(normalized_score, 2)}")
        return round(normalized_score, 2)
    
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
    
    def set_report(self, date):
        report = MarketReport()
        report.set_indicator_data(
            "ShillerPEIndicator",
                {
                    "daily_cape": round(self.daily_cape, 2),
                    "cape_average": round(self.cape_average, 2),
                    "promedio_cape_30": round(self.promedio_cape_30, 2),
                    "dev_cape_30": round(self.desv_cape_30),
                    "url": self.url,
                    "normalized_score": round(self.normalize(date), 2)
                }, str(date)
            )

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