from unittest.mock import MagicMock
from indicators.FearGreedIndicator import FearGreedIndicator
import pytest

from indicators.test.conftest import fetch_error

######################### Test basicos para FearGreedIndicator #########################

def test_fetch_data_valida(fetch_ok):
    indicador = FearGreedIndicator(fetch_fn=fetch_ok)
    resultado = indicador.fetch_data()
    assert resultado.value == 70

def test_normalize_valido(fetch_ok):
    indicador = FearGreedIndicator(fetch_fn=fetch_ok)
    assert indicador.normalize() == 0.3

######################### Test intermedios para FearGreedIndicator #########################

def test_fetch_data_error(fetch_error):
    indicador = FearGreedIndicator(fetch_fn=fetch_error)
    assert indicador.fetch_data() is None

def test_normalize_falla(fetch_error):
    indicador = FearGreedIndicator(fetch_fn=fetch_error)
    assert indicador.normalize() == 0

######################### Test avanzados para FearGreedIndicator #########################

# Valores invalidos no esperados, fuera de rango
@pytest.mark.parametrize("valor_fuera_de_rango", [-70, -1, -25, 105, 125])
def test_valores_fuera_de_rango_lanza_excepcion(valor_fuera_de_rango):
    class MockFGI:
        def __init__(self, value):
            self.value = value
            self.description = "Test"
            self.last_update = "2025-07-21"

    fetch_mock_exception = lambda: MockFGI(valor_fuera_de_rango)
    indicador = FearGreedIndicator(fetch_fn=fetch_mock_exception)

    # verificamos que se lanza la excepcion al obtener datos fuera de rango
    resultado = indicador.fetch_data()
    assert resultado is None # Porque la excepcion se atrapa dentro de la clase y entonces devuelve un None en el Exception

# Valores invalidos manejados por normalize
@pytest.mark.parametrize("valor_invalido", [-1, 101, None])
def test_normalize_con_valores_invalidos(valor_invalido):
    class MockFGI:
        def __init__(self, value): self.value = value
        description = "Test"
        last_update = "2025-07-22"

    fetch_mock = lambda: MockFGI(valor_invalido)
    indicator = FearGreedIndicator(fetch_fn=fetch_mock)

    score = indicator.normalize()
    assert score == 0

# Valores validos esperados, dentro del rango
@pytest.mark.parametrize("valor, esperado", [
    (75, 0.25),
    (55, 0.45),
    (25, 0.75),
    (20, 0.80),
    (100, 0.0),
    (0, 1.0)
])
def test_normalize_parametrizado(valor, esperado):
    mock_fgi = MagicMock()
    mock_fgi.value = valor
    mock_fgi.description = "mock"
    mock_fgi.last_update = "2025-07-21"

    indicador = FearGreedIndicator(fetch_fn=lambda: mock_fgi)
    assert indicador.normalize() == esperado

# Test para comprobar el comportamiento del indicador despues del nuevo calculo
def test_normalize_valor_medio():
    mock_fgi = MagicMock()
    mock_fgi.value = 50
    mock_fgi.description = "mock"
    mock_fgi.last_update = "2025-07-21"

    indicador = FearGreedIndicator(fetch_fn=lambda: mock_fgi)
    assert indicador.normalize() == 0.5  # (100 - 50) / 100

# Se pueden agregar test parametrizados para normalize fuera de rango como en fetch_data

###### Test para el metodo get_current_indicator #####
def test_get_current_indicator_valido(capsys):
    mock_fgi = MagicMock()
    mock_fgi.value = 53
    mock_fgi.description = "mock"
    mock_fgi.last_update = "2025-09-05"
    
    FearGreedIndicator(fetch_fn=lambda: mock_fgi).get_current_indicator()
    captured = capsys.readouterr()
    assert "Valor actual del CNN Fear & Greed" in captured.out # El primer print del metodo se valida

def test_get_current_indicator_none(capsys):
    FearGreedIndicator(fetch_fn=lambda: None).get_current_indicator()
    captured = capsys.readouterr()
    assert "No se pudo obtener el valor de Fear & Greed" in captured.out # El mensaje de error se valida