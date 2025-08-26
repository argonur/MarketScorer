from datetime import datetime
from indicators.IndicatorModule import IndicatorModule
from config.config_loader import get_config
import yfinance as yf

config = get_config() # Instanciamos la configuración global para poder acceder a ella
vix_weight = config.get('weights',{}).get('vix',{})

class VixIndicator(IndicatorModule):
    # Constructor
    def __init__(self, yf_client = None, config_data = None, vix_min = None, vix_max = None):
        self.config = config_data or get_config()
        vix_config = self.config.get('indicators',{}).get('vix',{})

        self.vix_min = vix_min if vix_min is not None else vix_config.get('min',{})
        self.vix_max = vix_max if vix_max is not None else vix_config.get('max',{})
        # cliente mockeable
        self.yf_client = yf_client or yf

    def fetch_data(self):
        try:
            ticker = self.yf_client.Ticker("^VIX")
            # Buscamos valors de los ultimos 5 dias habiles
            history = ticker.history(period = "5d")
            if not history.empty:
                today = datetime.today().date()
                fechas = history.index.date
            # Filtramos solo los dias con mercado cerrado y habiles, se excluye si esta abierto
                if today in fechas:
                    last_close = history.loc[history.index.date == today, 'Close'].iloc[-1]
                else:
                    last_close = history.loc[history.index.date < today, 'Close'].iloc[-1]
                return last_close
            else:
                raise ValueError("No se obtuvieron datos del ultimo cierre")
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