from indicators.IndicatorModule import IndicatorModule
from config.config_loader import get_config
import yfinance as yf
import data.market_dates as md
from utils.MarketReport import MarketReport
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_config()
# Obtenemos el valor del periodo para SMA desde el modulo de configuracion
periodo_sma = config.get('indicators',{}).get('spx',{}).get('sma_period')
SIMBOL = "^SPX"
start_date, end_date = md.yfinance_window_for_last_close()

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

        self._last_calculated_date = None
        self.sma_value = None
        self.last_close = None
        self.ratio_normalize = None

        # Cliente yf mockeable
        self.yf_client = yf_client or yf

    def _is_cached(self, date):
        return self._last_calculated_date == date and self.sma_value is not None
    
### Metodo independiente para obtener el ultimo cierre ###
    def get_last_close(self, SIMBOL, date):
        # Metodo para obtener el valor del ultimo cierre del indice S&P 500
        try:
            logger.info(F" -> Fecha last_close: {date}")
            sp500 = self.yf_client.Ticker(SIMBOL)
            datos = sp500.history(start=start_date, end=end_date, auto_adjust=True)

            if datos.empty:
                print("No se obtuvieron datos para el S&P 500.")
                return None
            ultimo_cierre = float(datos['Close'].iloc[0])
            logger.info(f" -> Last Close: {ultimo_cierre}")
            self.last_close = ultimo_cierre
            return ultimo_cierre
        except Exception as e:
            print(f"Error al obtener el ultimo cierre: {e}")
            raise
    
    def fetch_data(self, date):
        try:
            if self._is_cached(date):
                logger.info(f"Datos ya calculados para SMA-{periodo_sma}.... Usando caché")
                return self.sma_value
            logger.info(f" -> Fecha a usar: {date}") # loggers unicamente son para debug visual
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
            self.sma_value = sma
            self._last_calculated_date = date
            self.set_report(date)
            return sma

        except Exception as e:
            print(f"Hubo un error al obtener datos de la API: {e}")
            raise
    
    def normalize(self, date):
        try:
            if not self._is_cached(date):
                logger.warning(f"[SPX | Normalize]: Recalculando....")
                
            sma = self.fetch_data(date)
            # Validamos antes de hacer las operaciones
            if sma:
                ultimo_cierre = self.get_last_close(SIMBOL, date)
            else:
                raise ValueError("No se pudo calcular la SMA")

            if ultimo_cierre is None:
                raise ValueError("No se pudo obtener el ultimo cierre")

            # Obtenemos el ratio
            ratio = (ultimo_cierre - sma) / sma
            # Evaluar y normalizar segun la formula
            if ratio <= self.lower_ratio:
                ratio = 1.0
                return ratio
            elif ratio >= self.upper_ratio:
                ratio = 0.0
                return ratio
            if self.lower_ratio < ratio < self.upper_ratio:
                ratio = (self.upper_ratio - ratio) / (self.upper_ratio - self.lower_ratio)
                return ratio
            logger.warning(f"[SPX]: Ratio Value es: {ratio}")
            self.ratio_normalize = ratio
        except Exception as e:
            print(f"Hubo un error al normalizar los valores: {e}")
            raise

    def set_report(self, date):
        report = MarketReport()
        report.set_indicator_data("SPXIndicator",
                {
                    "sma_period": self.sma_period,
                    "sma_value": round(self.sma_value, 2),
                    "normalized_value": round(self.normalize(date), 2),
                    "last_close": round(self.last_close, 2)
                }, str(date)
                )
    
if __name__ == "__main__":
    try:
        indicador = SPXIndicator()
        
        print(f"Periodo de SMA: {periodo_sma}")
        print(f"Calculo SMA-{periodo_sma} de SPX: {indicador.fetch_data():.2f}")
        print(f"Ultimo cierre: {indicador.get_last_close(SIMBOL):.2f}")
        print(f"El score es de: {indicador.normalize():.2f}")
    except Exception as e:
        print(f"Hubo un error en el sistema: {e}")