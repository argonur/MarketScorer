from email import message
from unittest.mock import MagicMock
from indicators.FearGreedIndicator import FearGreedIndicator
import pytest
from datetime import date

# Definición del objeto FearGreedRecord
class MockFGI:
    def __init__(self, value, description="Test Description", last_update_str="2025-01-01"):
        self.value = value
        self.description = description
        self.last_update = last_update_str

######################### Test basicos para FearGreedIndicator #########################

def test_fetch_data_valida():
    """Test que verifica fetch_data con un valor válido."""
    fecha = date(2025, 12, 15)
    mock_fgi = MockFGI(value=70)
    # Crear la función mock para inyectar
    fetch_mock = MagicMock(return_value=mock_fgi)

    indicador = FearGreedIndicator(fetch_fn=fetch_mock)
    resultado = indicador.fetch_data(fecha)

    # Verificar que la función mock fue llamada con la fecha correcta
    fetch_mock.assert_called_once_with(fecha)
    # Verificar que el resultado sea el esperado
    assert resultado == mock_fgi
    assert resultado.value == 70
    # Verificar que los datos internos se actualizaron
    assert indicador.fgi_value == mock_fgi
    assert indicador._last_calculated_date == fecha

def test_normalize_valido(fetch_ok):
    fecha = date(2025, 12, 15)
    mock_fgi = MockFGI(value=70) # Se entiede que normalizado -> (100 - 70) / 100 = 0.3
    fetch_mock = MagicMock(return_value = mock_fgi)
    indicador = FearGreedIndicator(fetch_fn=fetch_mock)
    # fetch_data debe ser llamado internamente si no esta cacheado
    normalized_result = indicador.normalize(fecha)
    fetch_mock.assert_called_once_with(fecha)

    assert normalized_result == 0.3
    assert indicador.fg_normalized == 0.3

######################### Test intermedios para FearGreedIndicator #########################

def test_fetch_data_error(fetch_error):
    fecha = date(2025, 12, 15)
    fetch_mock = MagicMock(return_value = None)
    indicador = FearGreedIndicator(fetch_fn=fetch_mock)
    assert indicador.fetch_data(fecha) is None
    assert indicador.fgi_value is None

def test_normalize_falla():
    """Test que verifica que normalize devuelva None si fetch_data falla."""
    fecha = date(2025, 12, 15)
    fetch_mock = MagicMock(return_value=None) # fetch_data fallará

    indicador = FearGreedIndicator(fetch_fn=fetch_mock)
    score = indicador.normalize(fecha)

    assert score is None

######################### Test avanzados para FearGreedIndicator #########################

# Valores invalidos no esperados, fuera de rango
@pytest.mark.parametrize("valor_fuera_de_rango", [-70, -1, -25, 105, 125])
def test_valores_fuera_de_rango_lanza_excepcion(valor_fuera_de_rango):
    fecha = date(2025, 12, 15)
    mock_fgi = MockFGI(value=valor_fuera_de_rango)
    fetch_mock = MagicMock(return_value = mock_fgi)

    fetch_mock_exception = lambda: MockFGI(valor_fuera_de_rango)
    fecha = MockFGI(valor_fuera_de_rango).last_update
    indicador = FearGreedIndicator(fetch_fn=fetch_mock_exception)

    # verificamos que se lanza la excepcion al obtener datos fuera de rango
    resultado = indicador.fetch_data(fecha)
    assert resultado is None # Porque la excepcion se atrapa dentro de la clase y entonces devuelve un None en el Exception

# Valores invalidos manejados por normalize
@pytest.mark.parametrize("valor_invalido", [-1, 101, None])
def test_normalize_con_valores_invalidos(valor_invalido):
    fecha = date(2025, 12, 15)
    indicador = FearGreedIndicator(fetch_fn=None)
    indicador._last_calculated_date = fecha # Marcamos la fecha como calculada
    indicador.fgi_value = None # Forzamos un estado invalido para fg_value

    from unittest.mock import patch
    with patch.object(indicador, 'fetch_data') as mock_fetch_data_method:
        # Simulamos que fetch_data no cambia el estado interno o lo deja como None
        mock_fetch_data_method.return_value = None # Simula fallo o estado no cambiado

        # Aseguramos el estado antes de llamar a normalize
        indicador._last_calculated_date = fecha
        indicador.fgi_value = None

        # Llamamos a normalize
        score = indicador.normalize(fecha)

        # fetch_data debería haberse llamado
        mock_fetch_data_method.assert_called_once_with(fecha)
        # fetch_data retornó None, por lo tanto, fgi_value sigue siendo None (o fetch_data no lo cambió)
        # La verificación `if self.fgi_value is None` dentro de normalize (después de fetch_data)
        # debería evaluar a True y lanzar ValueError, que es capturado por el except y retorna None
        assert score is None

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
    fecha = date(2025, 12, 15)
    mock_fgi = MockFGI(value=valor)
    fetch_mock = MagicMock(return_value = mock_fgi)
    indicador = FearGreedIndicator(fetch_fn = fetch_mock)
    normalized_value = indicador.normalize(fecha)

# Test para comprobar el comportamiento del indicador despues del nuevo calculo
def test_normalize_valor_medio():
    fecha = date(2025, 12, 15)
    mock_fgi = MockFGI(value=50)
    fetch_mock = MagicMock(return_value=mock_fgi)

    indicador = FearGreedIndicator(fetch_fn=fetch_mock)
    assert indicador.normalize(fecha) == 0.5  # (100 - 50) / 100

# Se pueden agregar test parametrizados para normalize fuera de rango como en fetch_data

########## Tests opcionales/temporales para los loggers ##########

def test_logger_info_en_fetch_data(fetch_ok, caplog):
    fecha = date(2025, 12, 15)
    indicator = FearGreedIndicator(fetch_fn=fetch_ok)
    with caplog.at_level("INFO"):
        indicator.fetch_data(fecha)
    assert any("Fecha a usar" in message for message in caplog.messages)

# --- Test de caché ---

def test_fetch_data_cache_hit():
    """Test que verifica que se use la caché si los datos ya fueron calculados."""
    fecha = date(2025, 12, 15)
    mock_fgi = MockFGI(value=70)
    fetch_mock = MagicMock(return_value=mock_fgi)

    indicador = FearGreedIndicator(fetch_fn=fetch_mock)

    # Primera llamada -> debe llamar a fetch_mock
    resultado1 = indicador.fetch_data(fecha)
    assert fetch_mock.call_count == 1
    assert resultado1.value == 70

    # Segunda llamada con la misma fecha -> debe usar caché, NO llamar a fetch_mock
    resultado2 = indicador.fetch_data(fecha)
    assert fetch_mock.call_count == 1 # Conteo sigue siendo 1
    assert resultado2 == resultado1 # Mismo objeto retornado

def test_fetch_data_cache_miss_different_date():
    """Test que verifica que no se use la caché si la fecha cambia."""
    fecha1 = date(2025, 12, 15)
    fecha2 = date(2025, 12, 16)
    mock_fgi1 = MockFGI(value=70)
    mock_fgi2 = MockFGI(value=30)
    fetch_mock = MagicMock()
    fetch_mock.side_effect = [mock_fgi1, mock_fgi2] # Devolver 70, luego 30

    indicador = FearGreedIndicator(fetch_fn=fetch_mock)

    resultado1 = indicador.fetch_data(fecha1)
    assert fetch_mock.call_count == 1
    assert resultado1.value == 70

    resultado2 = indicador.fetch_data(fecha2)
    assert fetch_mock.call_count == 2 # Conteo incrementa
    assert resultado2.value == 30