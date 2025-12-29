from fear_and_greed import get as get_fear_greed_current
from utils.MarketReport import MarketReport
from indicators.IndicatorModule import IndicatorModule
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constructor de la clase FearGreedIndicator, tambien se le conoce como argumentos de funcion
class FearGreedIndicator(IndicatorModule):
    def __init__(self, fetch_fn=get_fear_greed_current):
        """ Inyección de dependencia:
        - fetch_fn -> Función externa que retorna el valor de fgi
        """
        self.fetch_fn = fetch_fn
        self._last_calculated_date = None
        self.fgi_value = None
        self.fg_normalized = None

    def _is_cached(self, date):
        return self._last_calculated_date == date and self.fgi_value is not None
        

    def fetch_data(self, date): 
        try:
            if self._is_cached(date):
                logger.info(f"Datos ya calculados para {date}.... Usando caché")
                return self.fgi_value
            logger.info(f" -> Fecha a usar: {date}")
            fgi = self.fetch_fn()
            if not (0 <= fgi.value <= 100):
                raise ValueError(f"Valor fuera de rango esperado: {fgi.value}")
            self.fgi_value = fgi
            self._last_calculated_date = date
            logger.info(f"[FG] Valor Crudo -> {round(fgi.value)}")
            self.set_report(date)
            return fgi
        except Exception as e: 
            print(f"Error al obtener el valor actual: {e}") 
        return None 
    
    def normalize(self, date):
        try:
            if not self._is_cached(date):
                logger.warning(f"[FG | Normalize]: Recalculando.....")
            data = self.fetch_data(date)
            if data and data.value is not None:
                fg_normalize = (100 - data.value.__round__()) / 100 # Para obtener un numero entre 0 y 1 en decimal
                return fg_normalize
        except Exception as e:
            logger.warning(f"Datos insuficientes: {e}")
            return None
        
    def set_report(self, date):
        report = MarketReport()
        report.set_indicator_data("FearGreedIndicator",
                {
                    "raw_value": round(self.fgi_value.value),
                    "raw_description": self.fgi_value.description,
                    "normalized_value": self.normalize(date),
                }, str(date)
                )

if __name__ == "__main__":
    indicator = FearGreedIndicator()
    print("Resultado normalizado:", indicator.get_score())
