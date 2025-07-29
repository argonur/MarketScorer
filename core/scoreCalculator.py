from typing import Callable, List, Dict, Any
from indicators.IndicatorModule import IndicatorModule
from indicators.FearGreedIndicator import FearGreedIndicator

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

            if weight <= 0:
                raise ValueError(f"El peso para: '{name}' debe ser mayor que cero (actual: {weight})")
            
            total_weight += weight
            if total_weight != 1.0:
                raise ValueError(f"El resultado de la suma de los pesos no es 1.0 (actual: {total_weight})")

            score = self.scorer_fn(indicator)


            if score is None:
                raise ValueError(f"El indicador '{name}' retornó un score Nulo")
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Score fuera de rango para: '{name}': {score}")

            score_final += (score * 100) * weight
            
            #print(f"Total de pesos: {total_weight}")
            #print(f"Score antes del final: {score_final}")

        return score_final / total_weight

        
### Programa principal ###
if __name__ == "__main__":
    fear_greed = FearGreedIndicator()

    #Lista de indicadores
    indicadores = [fear_greed]

    #Pesos manuales
    pesos = {
        "FearGreedIndicator": 1.0
    }

    # Calculadora Score
    try:
        calculator = ScoreCalculator(indicadores, pesos)
        total = calculator.calculate_score()
        print(f"Score final: {total:.1f}")
    except Exception as e:
        print(f"[Error en el calculo del score]:\n{e}")