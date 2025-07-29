from multiprocessing import Value
import pytest
from unittest.mock import MagicMock

from core.scoreCalculator import ScoreCalculator

# Casos validos
def test_score_calculator_valid():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.8
    # get_score es la funcion lamda del constructor de la clase

    indicators = [mock_indicator]
    weights = {"MagicMock": 1.0}

    calculator = ScoreCalculator(indicators, weights)
    assert calculator.calculate_score() == 80.0

# Caso, Manejo de error por pesos faltantes -> sin indicadores
def test_missing_weight_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.5
    indicators = [mock_indicator]
    weights = {} # Sin pesos

    with pytest.raises(ValueError, match="Falta peso para indicador"):
        ScoreCalculator(indicators, weights).calculate_score()

# Caso, Manejo de error por pesos faltantes
def test_missing_indicator_weight_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.5
    indicators = [mock_indicator]

    # No se incluye el peso para 'MagicMock', así que debe fallar
    weights = {"FearGreedIndicator": 1.0}

    with pytest.raises(ValueError, match="Falta peso para indicador"):
        ScoreCalculator(indicators, weights).calculate_score()

# Caso, Manejo error por peso = 0.0
def test_zero_weight_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 1.0
    indicators = [mock_indicator]
    weights = {"MagicMock": 0.0}

    with pytest.raises(ValueError, match="debe ser mayor que cero"):
        ScoreCalculator(indicators, weights).calculate_score()

# Caso, la suma de los pesos debe ser 1.0
def test_all_weights_be_one():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.71
    indicators = [mock_indicator]
    weights = {"MagicMock": 0.5}

    with pytest.raises(ValueError, match="los pesos no es 1.0"):
        ScoreCalculator(indicators, weights).calculate_score()

# Caso, Manejo de score nulo
def test_nule_score_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = None
    indicators = [mock_indicator]
    weights = {"MagicMock": 1.0}

    with pytest.raises(ValueError, match="retornó un score Nulo"):
        ScoreCalculator(indicators, weights).calculate_score()

# Caso, score fuera de rango
def test_score_out_of_range_raises_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 1.5
    indicators = [mock_indicator]
    weights = {"MagicMock": 1.0}

    with pytest.raises(ValueError, match="Score fuera de rango"):
        ScoreCalculator(indicators, weights).calculate_score()