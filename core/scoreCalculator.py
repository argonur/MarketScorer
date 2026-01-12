from datetime import date
from typing import Callable, List, Dict, Optional
from indicators.IndicatorModule import IndicatorModule
from indicators.FearGreedIndicator import FearGreedIndicator
from indicators.spxIndicator import SPXIndicator
from indicators.vixIndicator import VixIndicator
from indicators.shillerPEIndicator import ShillerPEIndicator
from data.market_dates import get_last_trading_close
from utils.validatedDates import get_a_validated_date
from utils.MarketReport import MarketReport
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config.config_loader import get_config

config = get_config() # Obtener la configuración

class ScoreCalculator:
    def __init__(self, indicators: List[IndicatorModule], weights: Dict[str, float], scorer_fn: Callable[[IndicatorModule, date], float] = None ):
        """
        Parámetros:
        - indicators: Lista de instancias de indicadores que heredan de IndicatorModule
        - weights: Diccionario con los nombres de los indicadores y su peso
        - scorer_fn: Funcion opcional para obtener el score de un indicador con una fecha (utilidad para mocking)
        """
        self.indicators = indicators
        self.weights = weights
        self.scorer_fn = scorer_fn if scorer_fn else lambda indicator, d: indicator.get_score(d)
        self._last_score = None # Guardar el ultimo calculo
        self._last_calculated_date = None

    def _is_cached(self, date):
        return self._last_calculated_date == date and self._last_score is not None

    def calculate_score(self, date: Optional[date] = None):
        if self._is_cached(date):
            logger.info(f"Datos ya calculados para {date}.... Usando caché")
            return self._last_score
        if date is None:
            logger.warning(f"[SC]Fecha no establecida.")
            logger.info(f"Buscando ultimo cierre habil....")
            date = get_last_trading_close().date()
        else:
            logger.info(f"Buscando datos para: {date}....")
        logger.info(f" -> Fecha a calcular {date}")
        if not get_a_validated_date(str(date)):
            raise ValueError(f"Invalid Date")

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

            score = self.scorer_fn(indicator, date)

            if score is None:
                raise ValueError(f"El indicador '{name}' retornó un score Nulo")
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Score fuera de rango para: '{name}': {score}")

            score_final += (score * 100) * weight    
        #print(f"Total de pesos: {total_weight}")
            #print(f"Score antes del final: {score_final}")
        if total_weight != 1.0:
            raise ValueError(f"El resultado de la suma de los pesos no es 1.0 (actual: {total_weight})")
        score_final = score_final / total_weight
        #self._last_score = score_final / total_weight
        self._last_score = score_final
        self._last_calculated_date = date

        # Guardar en MarketReport
        report = MarketReport()
        report.set_data("score_calculator", round(score_final), str(date)) # El valor del calculo final
        return self._last_score
    
    @classmethod
    def from_global_config(cls):
        """
        Fabrica un ScoreCalculator leyendo:
        1. Configuración global de pesos
        2. Instancias de los indicadores por defecto
        """
        # Instanciar indicadores
        indicators = [
            SPXIndicator(),
            FearGreedIndicator(),
            VixIndicator(),
            ShillerPEIndicator()
        ]

        # Mapear pesos según nombre de clase
        pesos = {
            type(ind).__name__: valid_weight(key)
            for ind, key in [
                (indicators[0], "spx"),
                (indicators[1], "fear_greed"),
                (indicators[2], "vix"),
                (indicators[3], "shiller"),
            ]
        }
        return cls(indicators=indicators, weights=pesos)

    @staticmethod
    def get_global_score(rounded: bool = False, date: Optional[date] = None) -> float:
        """
        Calcula el score usando la configuración global.
        Si rounded=True, devuelve el valor redondeado al entero más cercano.
        Si date es None, se usa el último cierre hábil.
        """
        calculator = ScoreCalculator.from_global_config()
        #date = "2025-12-22"
        raw_score = calculator.calculate_score(date)
        return round(raw_score) if rounded else raw_score


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
    # Calculadora Score
    try:
        total = ScoreCalculator.get_global_score(rounded=True)
        print(f"Score final: {total}")
    except Exception as e:
        print(f"❌ Error crítico en la configuración\n{e}")