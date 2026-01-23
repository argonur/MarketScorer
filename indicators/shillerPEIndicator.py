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
                return self.daily_cape
            # Descargar el archivo mas reciente
            filepath = download_latest_file(base_url=URL, file_name=NAME, save_dir=PATH_DIR)
            if not filepath:
                raise RuntimeError("No se pudo descargar el archivo Shiller PE")

            self._process_data(filepath, date)
            self._process_data_30(filepath, date)

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
            self.fetch_data(date)

        # Ahora, normalizar los datos ya calculados.
        normalized_score = self.normalize(date)
        return round(normalized_score, 2)
    
    def _process_data(self, file_path, date=None):
        try:
            # Detectar extensión y elegir engine
            ext = str(file_path).split(".")[-1].lower()
            engine = "xlrd" if ext == "xls" else "openpyxl"
            # Leer el archivo
            df = pd.read_excel(file_path, sheet_name="Data", engine=engine)
            if date:
                self.cape_average = self.calculate_cape_average(df, date, MAX_VALUE)
            else:
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
    
    def _process_data_30(self, file_path, date=None):
        ext = str(file_path).split(".")[-1].lower()
        engine = "xlrd" if ext == "xls" else "openpyxl"
        df = pd.read_excel(file_path, sheet_name="Data", engine=engine)
        if date:
            self.promedio_cape_30, self.desv_cape_30 = self.calculate_cape_30(df, date, 360)
        else:    
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
        data = sp500.history(start=date, end=end_date, auto_adjust=True)
        if data.empty:
            print("❌ No se pudieron obtener datos del índice S&P 500")
            return None
        return float(data['Close'].iloc[0])
    
    def parser_shiller_dates_searcher(self, df):
        """1. Convertir la primera columna del archivo ShillerPE a datetime.
            - El formato esperado es -> YYYY - MM
        """
        fechas = pd.to_datetime(df.iloc[:, 0].astype(str), format="%Y.%m", errors="coerce")
        df = df.assign(fecha=fechas)
        return df
    
    def filter_until_date(self, df, target_date):
        """
            - Filtrar el DateFrame hasta la fecha objetivo
            - target_date debe ser datetime o string con un formato compatible
        """
        target = pd.to_datetime(target_date)
        period = target.to_period("M")

        # Si la fecha no es el ultimo dia del mes, retroceder un mes
        if target.day != period.days_in_month:
            period = period - 1
        target_ts = period.to_timestamp(how="end")
        return df[df["fecha"] <= target_ts]
    
    def extract_numeric_column(self, df, col_index, window_size):
        """
            Extraer una columna numerica del DataFrame, limpia los NaN y devuelve las ultimas `window_size` filas
        """
        col = pd.to_numeric(df.iloc[:, col_index], errors="coerce").dropna()
        return col.tail(window_size)
    
    # Funciones especificas
    def calculate_cape_average(self, df, target_date, max_value=120):
        df = self.parser_shiller_dates_searcher(df)
        df = self.filter_until_date(df, target_date)
        values = self.extract_numeric_column(df, 10, max_value)
        return values.mean() if not values.empty else None

    def calculate_cape_30(self, df, target_date, window_size=360):
        df = self.parser_shiller_dates_searcher(df)
        df = self.filter_until_date(df, target_date)
        values = self.extract_numeric_column(df, 12, window_size)
        promedio = values.mean() if not values.empty else None
        desv = values.std() if not values.empty else None
        return promedio, desv
    
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