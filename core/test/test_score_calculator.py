import pytest
from unittest.mock import MagicMock
from unittest import mock

from core.scoreCalculator import ScoreCalculator, valid_weight

# Fixture para el test_valid_weights
@pytest.fixture
def valid_weights():
    return {
        "FearGreedIndicator": valid_weight('fear_greed'),
        "SPXIndicator": valid_weight('spx'),
        "VixIndicator": valid_weight('vix'),
        "ShillerPEIndicator": valid_weight('shiller')
    }

DATE_BACKTESTING = "2025-12-17"

# Casos validos
def test_score_calculator_valid():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.8
    # get_score es la funcion lamda del constructor de la clase

    indicators = [mock_indicator]
    weights = {"MagicMock": 1.0}

    calculator = ScoreCalculator(indicators, weights)
    assert calculator.calculate_score(DATE_BACKTESTING) == 80.0

# Caso, Manejo de error por pesos faltantes -> sin indicadores
def test_missing_weight_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.5
    indicators = [mock_indicator]
    weights = {} # Sin pesos

    with pytest.raises(ValueError, match="Falta peso para indicador"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

# Caso, Manejo de error por pesos faltantes
def test_missing_indicator_weight_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.5
    indicators = [mock_indicator]

    # No se incluye el peso para 'MagicMock', así que debe fallar
    weights = {"FearGreedIndicator": 1.0}

    with pytest.raises(ValueError, match="Falta peso para indicador"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

# Caso, Manejo error por peso = 0.0
def test_zero_weight_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 1.0
    indicators = [mock_indicator]
    weights = {"MagicMock": 0.0}

    with pytest.raises(ValueError, match="debe ser mayor que cero"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

# Caso, la suma de los pesos debe ser 1.0
def test_all_weights_be_one():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.71
    indicators = [mock_indicator]
    weights = {"MagicMock": 0.5}

    with pytest.raises(ValueError, match="los pesos no es 1.0"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

# Caso, Manejo de score nulo
def test_nule_score_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = None
    indicators = [mock_indicator]
    weights = {"MagicMock": 1.0}

    with pytest.raises(ValueError, match="retornó un score Nulo"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

# Caso, score fuera de rango
def test_score_out_of_range_raises_error():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 1.5
    indicators = [mock_indicator]
    weights = {"MagicMock": 1.0}

    with pytest.raises(ValueError, match="Score fuera de rango"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

###### Errores con la Configuracion Global
def test_weights_by_global_configuration():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 1.0
    indicators = [mock_indicator]
    weights = {"MagicMock": 404} # 404 es el codigo de error que se obtiene si se solicita un peso que no existe

    with pytest.raises(ValueError, match="Hubo un problema al"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

# Caso, valida que los pesos de los indicadores sean validos
def test_valid_weights():
    mock_indicator_fg = MagicMock()
    mock_indicator_spx = MagicMock()
    mock_indicador_vix = MagicMock()
    mock_indicador_shiller = MagicMock()

    type(mock_indicator_fg).__name__ = "FearGreedIndicator"
    type(mock_indicator_spx).__name__ = "SPXIndicator"
    type(mock_indicador_vix).__name__ = "VixIndicator"
    type(mock_indicador_shiller).__name__ = "ShillerPEIndicator"

    valid_weight_fg = valid_weight('fear_greed')
    valid_weight_spx = valid_weight('spx')
    valid_weight_vix = valid_weight('vix')
    valid_weight_shiller = valid_weight('shiller')

    mock_indicator_fg.get_score.return_value = 0.4
    mock_indicator_spx.get_score.return_value = 0.28
    mock_indicador_vix.get_score.return_value = 0.08
    mock_indicador_shiller.get_score.return_value = 0.08

    indicators = [mock_indicator_fg, mock_indicator_spx, mock_indicador_vix, mock_indicador_shiller]

    weights = {
        "FearGreedIndicator": valid_weight_fg,
        "SPXIndicator": valid_weight_spx,
        "VixIndicator": valid_weight_vix,
        "ShillerPEIndicator": valid_weight_shiller
        }

    calculator = ScoreCalculator(indicators, weights)
    assert calculator.calculate_score(DATE_BACKTESTING).__round__() == 22

def test_wrong_weights():
    mock_indicator = MagicMock()
    mock_indicator.get_score.return_value = 0.43
    indicators = [mock_indicator]
    valid_weights_config = valid_weight('spy')
    weights = {"MagicMock": valid_weights_config }

    with pytest.raises(ValueError, match="Hubo un problema al"):
        ScoreCalculator(indicators, weights).calculate_score(DATE_BACKTESTING)

def test_get_global_score_sin_redondear(monkeypatch):
    # Mock de from_global_config para devolver un ScoreCalculator falso
    fake_calc = MagicMock()
    fake_calc.calculate_score.return_value = 42.7
    monkeypatch.setattr(ScoreCalculator, "from_global_config", classmethod(lambda cls: fake_calc))

    result = ScoreCalculator.get_global_score(rounded=False)

    # Debe devolver el valor crudo
    assert result == 42.7
    fake_calc.calculate_score.assert_called_once()


def test_get_global_score_redondeado(monkeypatch):
    fake_calc = MagicMock()
    fake_calc.calculate_score.return_value = 42.7
    monkeypatch.setattr(ScoreCalculator, "from_global_config", classmethod(lambda cls: fake_calc))

    result = ScoreCalculator.get_global_score(rounded=True)

    # Debe devolver el valor redondeado
    assert result == 43
    fake_calc.calculate_score.assert_called_once()
