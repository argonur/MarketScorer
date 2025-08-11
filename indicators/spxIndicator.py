from queue import Empty
from indicators.IndicatorModule import IndicatorModule
from config.config_loader import get_config
import yfinance as yf

config = get_config()
# Obtenemos el valor del periodo para SMA desde el modulo de configuracion
periodo_sma = config.get('indicators',{}).get('spx',{}).get('sma_period')
symbol = "^SPX"

class SPXIndicator(IndicatorModule):
    # Constructor
    def __init__(self, config, ticker_factory=yf.Ticker):
        """ Dependencias Inyectadas al indicador SPX.
        parametro "config": Configuración del indicador
        parametro "ticker_factory": Funcion para crear objetos Ticker
        """
        super().__init__()
        self.config = config
        self.ticker_factory = ticker_factory

        # Extracción de parametros de configuración
        spx_config = config.get('indicators', {}).get('spx',{})
        self.sma_period = spx_config.get('sma_period')
        self.upper_ratio = spx_config.get('upper_ratio')
        self.lower_ratio = spx_config.get('lower_ratio')
        pass
    
### Metodo independiente para obtener el ultimo cierre ###
    def obtener_ultimo_cierre(self, symbol = symbol):
        # Metodo para obtener el valor del ultimo cierre del indice S&P 500
        try:
            sp500 = yf.Ticker(symbol)
            hist = sp500.history(period="1d")
            if not hist.empty:
                ultimo_cierre = hist['Close'].iloc[-1]
                return ultimo_cierre
            else:
                print("No se obtuvieron datos")
                return None
        except Exception as e:
            print(f"Error: {e}")
    
    def fetch_data(self, symbol = symbol):
        try:
            ticker = yf.Ticker(symbol)

            # Descargar 300 dias bursatiles para asegurar los dias por defecto
            historical_data = ticker.history(period="300d")

            if historical_data.empty:
                raise ValueError("No se obtuvieron datos historicos")
            
            # Obtener precios de cierres
            cierres = historical_data['Close']
            if cierres.empty:
                raise ValueError("No se obtuvieron datos historicos")

            # Verificar datos suficientes
            if len(cierres) < periodo_sma:
                available = len(cierres)
                raise ValueError(f"Advertencia: Solo {available}/{periodo_sma} dias disponibles")
            else:
                sma = cierres.tail(periodo_sma).mean()
            return sma

        except Exception as e:
            print(f"Hubo un error al obtener datos de la API: {e}")
    
    def normalize(self):
        try:
            sma = self.fetch_data()
            # Validamos antes de hacer las operaciones
            if sma is None:
                raise ValueError("No se pudo obtener un valor SMA valido")
            ultimo_cierre = self.obtener_ultimo_cierre()

            if ultimo_cierre is None:
                raise ValueError("No se pudo obtener el ultimo cierre")
            upper_ratio = config.get('indicators',{}).get('spx',{}).get('upper_ratio')
            lower_ratio = config.get('indicators',{}).get('spx',{}).get('lower_ratio')
            score = None

            # Obtenemos el ratio
            ratio = (ultimo_cierre - sma) / sma
            # Evaluar y normalizar segun la formula
            if ratio <= lower_ratio:
                score = 1.0
                return score
            elif ratio >= upper_ratio:
                score = 0.0
                return score
            elif lower_ratio < ratio < upper_ratio:
                score = (upper_ratio - ratio) / (upper_ratio - lower_ratio)
                return score
        except Exception as e:
            print(f"Hubo un error al normalizar los valores: {e}")
            raise ValueError
    
if __name__ == "__main__":
    try:
        indicador = SPXIndicator(config=config)
        
        print(f"Periodo de SMA: {periodo_sma}")
        print(f"Calculo SMA-{periodo_sma} de SPX: {indicador.fetch_data():.2f}")
        print(f"Ultimo cierre: {indicador.obtener_ultimo_cierre():.2f}")
        print(f"El score es de: {indicador.normalize():.2f}")
    except Exception as e:
        print(f"Hubo un error en el sistema: {e}")