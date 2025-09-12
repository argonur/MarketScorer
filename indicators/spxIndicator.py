from queue import Empty
from indicators.IndicatorModule import IndicatorModule
from config.config_loader import get_config
import yfinance as yf
import data.market_dates as md

config = get_config()
# Obtenemos el valor del periodo para SMA desde el modulo de configuracion
periodo_sma = config.get('indicators',{}).get('spx',{}).get('sma_period')
SIMBOL = "^SPX"

class SPXIndicator(IndicatorModule):
    # Constructor
    def __init__(self, upper_ratio = None, lower_ratio = None, sma_period = None, yf_client = None, config_data = None):
        """ El objetivo es poder crear un objeto yf_client falso para mockear en las pruebas. """
        # Cargar configuracion mockeable para tests
        self.config = config_data or get_config()
        spx_config = self.config.get('indicators', {}).get('spx', {})
        
        self.upper_ratio = upper_ratio if upper_ratio is not None else spx_config.get('upper_ratio')
        self.lower_ratio = lower_ratio if lower_ratio is not None else spx_config.get('lower_ratio')
        self.sma_period = sma_period if sma_period is not None else spx_config.get('sma_period')

        # Cliente yf mockeable
        self.yf_client = yf_client or yf
    
### Metodo independiente para obtener el ultimo cierre ###
    def get_last_close(self, simbol=SIMBOL):
        # Metodo para obtener el valor del ultimo cierre del indice S&P 500
        try:
            start_date, end_date = md.yfinance_window_for_last_close()
            sp500 = self.yf_client.Ticker(simbol)
            datos = sp500.history(start=start_date, end=end_date, auto_adjust=True)

            if datos.empty:
                print("No se obtuvieron datos para el S&P 500.")
                return None
            ultimo_cierre = float(datos['Close'].iloc[0])
            return ultimo_cierre
        except Exception as e:
            print(f"Error al obtener el ultimo cierre: {e}")
            raise
    
    def fetch_data(self):
        try:
            ticker = self.yf_client.Ticker(SIMBOL)

            # Descargar 300 dias bursatiles para asegurar los dias por defecto
            historical_data = ticker.history(period="300d")

            if historical_data.empty:
                print("No se obtuvieron datos historicos")
                return None

            # Verificar si la columna 'Close' existe
            if 'Close' not in historical_data.columns:
                print("No se obtuvieron datos historicos")
                return None
            
            # Obtener precios de cierres
            cierres = historical_data['Close']

            # Verificar datos suficientes
            if len(cierres) < self.sma_period:
                available = len(cierres)
                raise ValueError(f"Advertencia: Solo {available}/{self.sma_period} dias disponibles")
                
            sma = cierres.tail(self.sma_period).mean()
            return sma

        except Exception as e:
            print(f"Hubo un error al obtener datos de la API: {e}")
            raise
    
    def normalize(self):
        try:
            sma = self.fetch_data()
            # Validamos antes de hacer las operaciones
            if sma:
                ultimo_cierre = self.get_last_close(SIMBOL)
            else:
                raise ValueError("No se pudo calcular la SMA")

            if ultimo_cierre is None:
                raise ValueError("No se pudo obtener el ultimo cierre")

            # Obtenemos el ratio
            ratio = (ultimo_cierre - sma) / sma
            # Evaluar y normalizar segun la formula
            if ratio <= self.lower_ratio:
                return 1.0
            elif ratio >= self.upper_ratio:
                return 0.0
            if self.lower_ratio < ratio < self.upper_ratio:
                return (self.upper_ratio - ratio) / (self.upper_ratio - self.lower_ratio)
        except Exception as e:
            print(f"Hubo un error al normalizar los valores: {e}")
            raise
    
if __name__ == "__main__":
    try:
        indicador = SPXIndicator()
        
        print(f"Periodo de SMA: {periodo_sma}")
        print(f"Calculo SMA-{periodo_sma} de SPX: {indicador.fetch_data():.2f}")
        print(f"Ultimo cierre: {indicador.get_last_close(SIMBOL):.2f}")
        print(f"El score es de: {indicador.normalize():.2f}")
    except Exception as e:
        print(f"Hubo un error en el sistema: {e}")