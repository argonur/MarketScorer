from email import message
from unittest.mock import MagicMock
from indicators.FearGreedIndicator import FearGreedIndicator
import pytest
from datetime import date

from indicators.test.conftest import fetch_error

######################### Test basicos para FearGreedIndicator #########################

def test_fetch_data_valida(fetch_ok):
    fecha = date(2025, 12, 15) # Simulamos haber definido una fecha la cual recibira el indicador FearGreed cuando sea llamada en ScoreCalculator.
    indicador = FearGreedIndicator(fetch_fn=fetch_ok)
    resultado = indicador.fetch_data(fecha)
    assert resultado.value == 70
    assert fecha == date(2025, 12, 15)

def test_normalize_valido(fetch_ok):
    fecha = date(2025, 12, 15)
    indicador = FearGreedIndicator(fetch_fn=fetch_ok)
    assert fecha == date(2025, 12, 15)
    assert indicador.normalize(fecha) == 0.3

######################### Test intermedios para FearGreedIndicator #########################

def test_fetch_data_error(fetch_error):
    fecha = date(2025, 12, 15)
    indicador = FearGreedIndicator(fetch_fn=fetch_error)
    assert indicador.fetch_data(fecha) is None

def test_normalize_falla(fetch_error):
    fecha = date(2025, 12, 15)
    indicador = FearGreedIndicator(fetch_fn=fetch_error)
    assert indicador.normalize(fecha) == 0

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
    fecha = MockFGI(valor_fuera_de_rango).last_update
    indicador = FearGreedIndicator(fetch_fn=fetch_mock_exception)

    # verificamos que se lanza la excepcion al obtener datos fuera de rango
    resultado = indicador.fetch_data(fecha)
    assert resultado is None # Porque la excepcion se atrapa dentro de la clase y entonces devuelve un None en el Exception

# Valores invalidos manejados por normalize
@pytest.mark.parametrize("valor_invalido", [-1, 101, None])
def test_normalize_con_valores_invalidos(valor_invalido):
    class MockFGI:
        def __init__(self, value): self.value = value
        description = "Test"
        last_update = "2025-07-22"

    fetch_mock = lambda: MockFGI(valor_invalido)
    fecha = MockFGI(valor_invalido).last_update
    indicator = FearGreedIndicator(fetch_fn=fetch_mock)

    score = indicator.normalize(fecha)
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
    fecha = mock_fgi.last_update
    assert indicador.normalize(fecha) == esperado

# Test para comprobar el comportamiento del indicador despues del nuevo calculo
def test_normalize_valor_medio():
    mock_fgi = MagicMock()
    mock_fgi.value = 50
    mock_fgi.description = "mock"
    mock_fgi.last_update = "2025-07-21"

    indicador = FearGreedIndicator(fetch_fn=lambda: mock_fgi)
    fecha = mock_fgi.last_update
    assert indicador.normalize(fecha) == 0.5  # (100 - 50) / 100

# Se pueden agregar test parametrizados para normalize fuera de rango como en fetch_data

########## Tests opcionales/temporales para los loggers ##########

def test_logger_info_en_fetch_data(fetch_ok, caplog):
    fecha = date(2025, 12, 15)
    indicator = FearGreedIndicator(fetch_fn=fetch_ok)
    with caplog.at_level("INFO"):
        indicator.fetch_data(fecha)
    assert any("Fecha a usar" in message for message in caplog.messages)