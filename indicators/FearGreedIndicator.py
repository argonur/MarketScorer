from fear_and_greed import get as get_fear_greed_current
from indicators.IndicatorModule import IndicatorModule

# Constructor de la clase FearGreedIndicator, tambien se le conoce como argumentos de funcion
class FearGreedIndicator(IndicatorModule):
    def __init__(self, fetch_fn=get_fear_greed_current):
        """ Inyección de dependencia:
        - fetch_fn -> Función externa que retorna el valor de fgi
        """
        self.fetch_fn = fetch_fn
        

    def fetch_data(self): 
        try: 
            fgi = self.fetch_fn()

            if not (0 <= fgi.value <= 100):
                raise ValueError(f"Valor fuera de rango esperado: {fgi.value}")
            return fgi
        except Exception as e: 
            print(f"Error al obtener el valor actual: {e}") 
        return None 
    
    def normalize(self):  
        data = self.fetch_data()
        if data and data.value is not None:
            return (100 - data.value.__round__()) / 100 # Para obtener un numero entre 0 y 1 en decimal
        return 0

    def get_current_indicator(self):
        fg_indicator = self.fetch_data()
        try:
            if fg_indicator is None:
                raise ValueError("No se pudo obtener el valor de Fear & Greed")
            print(f"Valor actual del CNN Fear & Greed Index: {round(fg_indicator.value)} ({fg_indicator.description})")
            print(f"Última actualización: {fg_indicator.last_update}")
        except Exception as e:
            print(f"[FG]: Ha ocurrido un error: {e}")

if __name__ == "__main__":
    indicator = FearGreedIndicator()
    indicator.get_current_indicator()
    print("Resultado normalizado:", indicator.get_score())
