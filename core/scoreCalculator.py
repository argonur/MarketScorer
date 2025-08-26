from typing import Callable, List, Dict
from indicators.IndicatorModule import IndicatorModule
from indicators.FearGreedIndicator import FearGreedIndicator
from indicators.spxIndicator import SPXIndicator
from indicators.vixIndicator import VixIndicator
from config.config_loader import get_config

config = get_config() # Obtener la configuración

class ScoreCalculator:
    def __init__(self, indicators: List[IndicatorModule], weights: Dict[str, float], scorer_fn: Callable[[IndicatorModule], float] = None):
        """
        Parámetros:
        - indicators: Lista de instancias de indicadores que heredan de IndicatorModule
        - weights: Diccionario con los nombres de los indicadores y su peso
        - scorer_fn: Funcion opcional para obtener el score de un indicador (utilidad para mocking)
        """
        self.indicators = indicators
        self.weights = weights
        self.scorer_fn = scorer_fn if scorer_fn else lambda indicator: indicator.get_score()

    def calculate_score(self):
        score_final = 0.0
        total_weight = 0.0

        for indicator in self.indicators:
            name = type(indicator).__name__

            if name not in self.weights:
                raise ValueError(f"Falta peso para indicador: {name}")

            weight = self.weights[name]

            if weight == 404:
                raise ValueError(f"❌ Hubo un problema al cargar los pesos desde Configuracion Global")

            if weight <= 0:
                raise ValueError(f"El peso para: '{name}' debe ser mayor que cero (actual: {weight})")
            
            total_weight += weight

            score = self.scorer_fn(indicator)

            if score is None:
                raise ValueError(f"El indicador '{name}' retornó un score Nulo")
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Score fuera de rango para: '{name}': {score}")

            score_final += (score * 100) * weight    
        #print(f"Total de pesos: {total_weight}")
            #print(f"Score antes del final: {score_final}")
        if total_weight != 1.0:
            raise ValueError(f"El resultado de la suma de los pesos no es 1.0 (actual: {total_weight})")
        return score_final / total_weight

def valid_weight(param):
    """Obtienemos el peso de un indicador desde la configuración global"""
    try:
        weights = config.get('weights', {})

        # Verifico si el parametro existe en los pesos
        if param in weights:
            print(f"El peso de {param} es: {weights[param]}")
            return weights[param]
        else:
            print(f"⚠️ Peso no encontrado para indicador: {param}")
            return 404
    except Exception as e:
        print(f"❌ Error crítico en la configuración: {str(e)}")
        return 500


### Programa principal ###
if __name__ == "__main__":
    fear_greed = FearGreedIndicator()
    spx_sma = SPXIndicator()
    vix = VixIndicator()

    fearGreed_weight = valid_weight('fear_greed')
    spx_weight = valid_weight('spx')
    vix_weight = valid_weight('vix')

    #Lista de indicadores
    indicadores = [spx_sma, fear_greed, vix]
    
    #Pesos obtenidos desde la configuración global
    pesos = { 
        "FearGreedIndicator": fearGreed_weight,
        "SPXIndicator": spx_weight,
        "VixIndicator": vix_weight
    }

    # Calculadora Score
    try:
        calculator = ScoreCalculator(indicadores, pesos)
        total = calculator.calculate_score().__round__()
        print(f"Score final: {total}")
    except Exception as e:
        print(f"❌ Error crítico en la configuración\n{e}")