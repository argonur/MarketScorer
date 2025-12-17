from datetime import date
from fear_and_greed import get as get_fear_greed_current
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
        

    def fetch_data(self, date): 
        try:
            logger.info(f" -> Fecha a usar: {date}")
            fgi = self.fetch_fn()
            if not (0 <= fgi.value <= 100):
                raise ValueError(f"Valor fuera de rango esperado: {fgi.value}")
            return fgi
        except Exception as e: 
            print(f"Error al obtener el valor actual: {e}") 
        return None 
    
    def normalize(self, date):  
        data = self.fetch_data(date)
        if data and data.value is not None:
            return (100 - data.value.__round__()) / 100 # Para obtener un numero entre 0 y 1 en decimal
        return 0

if __name__ == "__main__":
    indicator = FearGreedIndicator()
    print("Resultado normalizado:", indicator.get_score())
