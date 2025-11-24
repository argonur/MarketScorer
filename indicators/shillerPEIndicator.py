from indicators.IndicatorModule import IndicatorModule
from utils.file_downloader import download_latest_file
from data.market_dates import yfinance_window_for_last_close
from dotenv import load_dotenv
import yfinance as yf
import os
import pandas as pd

load_dotenv()
URL = os.getenv("SHELLER_PE_URL")
NAME = os.getenv("SHILLER_PE_ARCHIVE_NAME")
PATH_DIR = os.getenv("SAVE_PATH")
MAX_VALUE = 120
start_date, end_date = yfinance_window_for_last_close()
SYMBOL = "^SPX"

class ShellerPEIndicator(IndicatorModule):
    #Constructor
    def __init__(self):
        super().__init__()
        self.cape_average = None # Para almacenar el promedio calculado
        self.daily_cape = None
        self.url = URL
        self.last_close = None
        self.promedio_cape_30 = None
        self.desv_cape_30 = None

    def fetch_data(self):
        try:
            # Descargar el archivo mas reciente
            filepath = download_latest_file(base_url=URL, file_name=NAME, save_dir=PATH_DIR)
            if not filepath:
                print("❌ No se pudo obtener el archivo.")
                return
            self.process_data(filepath)
            self.process_data_30(filepath)

            # Obtener el ultimo cierre de S&P 500
            last_close_spx = round(self.get_last_close(SYMBOL), 2)
            self.daily_cape = round((last_close_spx / self.cape_average), 2)
            return self.daily_cape
        except Exception as e:
            print(e)

    def normalize(self):
        try:
            if self.desv_cape_30 <= 0.1:
                score = 1
            else:
                z = (self.daily_cape - self.promedio_cape_30) / self.desv_cape_30
                score = max(0, min(100, 100 - max(0, z) * 25)) / 100

            return score
        except Exception as e:
            print(e)

    
    def process_data(self, file_path):
        try:
            # Leer el archivo
            df = pd.read_excel(file_path, sheet_name="Data")
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
            
            # Calcular promedio
            promedio = val_obtenidos.mean()
            self.cape_average = promedio # Guardar el promedio en el atributo de clases
        except Exception as e:
            print(f"Error al abrir el archivo")
    
    def process_data_30(self, file_path):
        max_value_cape_30 = 360
        try:
            df = pd.read_excel(file_path, sheet_name="Data")
            columna_12 = df.iloc[:, 12]
            columna_numerica = pd.to_numeric(columna_12, errors="coerce")
            columna_limpia = columna_numerica.dropna()
            val_obtenidos = columna_limpia.tail(max_value_cape_30)
            if len(val_obtenidos) < max_value_cape_30:
                print(f"⚠️ Solo se encontraron {len(val_obtenidos)} valores válidos (se necesitan {max_value_cape_30}).")

            # Calcular promedio
            self.promedio_cape_30 = round(val_obtenidos.mean(), 2)
            self.desv_cape_30 = round(val_obtenidos.std(), 2)
            
        except Exception as e:
            print(e)

    def get_last_close(self, symbol):
        try:
            sp500 = yf.Ticker(symbol)
            data = sp500.history(start=start_date, end=end_date, auto_adjust=True)
            if data.empty:
                print("No se pudieron obtener datos del indice S&P 500")
                return None
            last_close = float(data['Close'].iloc[0])
            self.last_close = last_close
            return last_close
        except Exception as e:
            print("Error al obtener el ultimo cierre", e)

if __name__ == "__main__":
    try:
        indicator = ShellerPEIndicator()
        indicator.fetch_data()
        print(f"✅ Promedio de las últimas {MAX_VALUE} filas: {indicator.cape_average:.2f}")
        print(f"👉 El CAPE diario es: {indicator.daily_cape}")
        print("📍 Ultimo cierre de S&P 500:", round(indicator.last_close, 2))
        print(f"👉 Promedio de CAPE 30: {indicator.promedio_cape_30}")
        print(f"📍 Desviación estandar CAPE 30: {indicator.desv_cape_30}")

    except Exception as e:
        print(e)