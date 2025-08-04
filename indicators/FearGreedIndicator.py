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
            value = fgi.value.__round__() # Se redondea el valor de la API

            if not (0 <= fgi.value <= 100):
                raise ValueError(f"Valor fuera de rango esperado: {fgi.value}")

            print(f"Valor actual del CNN Fear & Greed Index: {value} ({fgi.description})")
            print(f"Última actualización: {fgi.last_update}") 
            return fgi
        except Exception as e: 
            print(f"Error al obtener el valor actual: {e}") 
        return None 
    
    def normalize(self):  
        data = self.fetch_data()
        if data and data.value is not None:
            return (100 - data.value.__round__()) / 100 # Para obtener un numero entre 0 y 1 en decimal
        return 0

if __name__ == "__main__":
    indicator = FearGreedIndicator()
    print("Resultado normalizado:", indicator.get_score())
