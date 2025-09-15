from datetime import datetime
from indicators.IndicatorModule import IndicatorModule
from config.config_loader import get_config
import data.market_dates as md
import yfinance as yf

config = get_config() # Instanciamos la configuración global para poder acceder a ella
vix_weight = config.get('weights',{}).get('vix',{})
SIMBOL = "^VIX"

class VixIndicator(IndicatorModule):
    # Constructor
    def __init__(self, yf_client = None, config_data = None, vix_min = None, vix_max = None):
        self.config = config_data or get_config()
        vix_config = self.config.get('indicators',{}).get('vix',{})

        self.vix_min = vix_min if vix_min is not None else vix_config.get('min',{})
        self.vix_max = vix_max if vix_max is not None else vix_config.get('max',{})
        # cliente mockeable
        self.yf_client = yf_client or yf

    def get_last_close(self, start_date, end_date) -> float | None:
        try:
            vix = self.yf_client.Ticker(SIMBOL)
            datos = vix.history(start=start_date, end=end_date, auto_adjust=True)
            if datos.empty:
                raise ValueError("Fallo al obtener datos de VIX.")
            return float(datos['Close'].iloc[0])
        except Exception as e:
            print(f"Error al obtener el ultimo cierre: {e}")
            return None

    def fetch_data(self) -> float | None:
        try:
            start_date, end_date = md.yfinance_window_for_last_close()
            last_close = self.get_last_close(start_date, end_date)
            if last_close is None:
                raise ValueError("No se obtuvieron datos de cierre.")
            
            return last_close
        except Exception as e:
            print(f"░ Fetch: {e}, ó no hay conexion a internet")
            return None
    
    def normalize(self):
        try:
            vix_actual = self.fetch_data()

            if vix_actual is None:
                raise ValueError("No se obtuvieron datos para normalizar")

            # Validamos que no caiga fuera de rango inferior o superior
            if vix_actual <= self.vix_min:
                print("Fuera de limite inferior...")
                return 0
            elif vix_actual >= self.vix_max:
                print("Fuera de limite superior...")
                return 1

            # Aplicamos la formula para obtener el score final
            score = (vix_actual - self.vix_min) / (self.vix_max - self.vix_min)
            return round(score, 2)
        except Exception as e:
            print(f"░ Normalize: {e}")
            return None

if __name__ == "__main__":
    try:
        indicador =  VixIndicator()
        print(f"Ultimo cierre Vix: {indicador.fetch_data():.2f}")
        print(f"Vix normalizado: {indicador.normalize()}")
    except Exception as e:
        print(f"█ Hubo un problema en la ejecución del modulo VixIndicator: {e}")