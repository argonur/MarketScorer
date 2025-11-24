import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from indicators.shillerPEIndicator import ShellerPEIndicator

# Ruta del archivo de prueba 
TEST_FILE_PATH = "tests/ie_data_2025-11-17.xlsx"

# Mock para yfinance.Ticker
class MockTicker:
    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start, end, auto_adjust=True):
        # Simular un DataFrame con un solo registro
        data = {
            'Close': [4800.0]  # Supongamos que el último cierre del S&P 500 es 4800.0
        }
        return pd.DataFrame(data, index=pd.to_datetime(['2025-11-17']))

@pytest.fixture
def indicator():
    """Fixture para crear una instancia de ShellerPEIndicator."""
    # Mockear download_latest_file para que devuelva una ruta fija
    with patch('indicators.shillerPEIndicator.download_latest_file', return_value=TEST_FILE_PATH):
        indicator = ShellerPEIndicator()
        # No inicializamos los atributos aquí, dejamos que fetch_data los calcule o falle
        yield indicator

@pytest.fixture
def mock_yf():
    """Fixture para mockear yfinance.Ticker."""
    with patch('yfinance.Ticker', new_callable=MagicMock) as mock_ticker:
        mock_ticker.return_value = MockTicker("mock_symbol")
        yield mock_ticker

# ---------- Test process_data ----------
def test_process_data_calcula_promedio(tmp_path):
    # Crear un Excel falso con 120 valores en la columna 10
    df = pd.DataFrame({i: range(200) for i in range(11)})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, sheet_name="Data", index=False)

    indicator = ShellerPEIndicator()
    indicator.process_data(file_path)

    assert indicator.cape_average is not None
    # El promedio de los últimos 120 valores de la columna 10 (0..199)
    esperado = pd.Series(range(80, 200)).mean()
    assert pytest.approx(indicator.cape_average, 0.01) == esperado

def test_process_data_menos_valores(tmp_path, capsys):
    # Crear 11 columnas, la última con pocos valores
    df = pd.DataFrame({i: range(3) for i in range(11)})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, sheet_name="Data", index=False)

    indicator = ShellerPEIndicator()
    indicator.process_data(file_path)

    captured = capsys.readouterr()
    assert "⚠️ Solo se encontraron" in captured.out
    assert indicator.cape_average == pytest.approx(1.0)  # promedio de [0,1,2]

# ---------- Test get_last_close ----------
@patch("indicators.shillerPEIndicator.yf.Ticker")
def test_get_last_close_devuelve_valor(mock_ticker):
    mock_df = pd.DataFrame({"Close": [4500.55]})
    mock_ticker.return_value.history.return_value = mock_df

    indicator = ShellerPEIndicator()
    valor = indicator.get_last_close("^SPX")

    assert valor == 4500.55

@patch("indicators.shillerPEIndicator.yf.Ticker")
def test_get_last_close_empty(mock_ticker, capsys):
    mock_ticker.return_value.history.return_value = pd.DataFrame()

    indicator = ShellerPEIndicator()
    valor = indicator.get_last_close("^SPX")

    assert valor is None
    captured = capsys.readouterr()
    assert "No se pudieron obtener datos" in captured.out

# ---------- Test fetch_data ----------
@patch("indicators.shillerPEIndicator.download_latest_file")
@patch.object(ShellerPEIndicator, "process_data")
@patch.object(ShellerPEIndicator, "get_last_close")
def test_fetch_data_calcula_daily_cape(mock_get_close, mock_process, mock_download):
    mock_download.return_value = "fake.xlsx"
    mock_process.side_effect = lambda filepath: setattr(indicator, "cape_average", 25.0)
    mock_get_close.return_value = 5000.0

    indicator = ShellerPEIndicator()
    indicator.fetch_data()

    assert indicator.daily_cape == pytest.approx(200.0)


# --- fetch_data: download_latest_file devuelve None ---
@patch("indicators.shillerPEIndicator.download_latest_file", return_value=None)
def test_fetch_data_sin_archivo(mock_download, capsys):
    indicator = ShellerPEIndicator()
    indicator.fetch_data()
    captured = capsys.readouterr()
    assert "❌ No se pudo obtener el archivo." in captured.out

# --- fetch_data: process_data lanza excepción ---
@patch("indicators.shillerPEIndicator.download_latest_file", return_value="fake.xlsx")
@patch.object(ShellerPEIndicator, "process_data", side_effect=Exception("fallo en process_data"))
def test_fetch_data_excepcion_process(mock_process, mock_download, capsys):
    indicator = ShellerPEIndicator()
    indicator.fetch_data()
    captured = capsys.readouterr()
    assert "fallo en process_data" in captured.out

# --- get_last_close: excepción en yfinance ---
@patch("indicators.shillerPEIndicator.yf.Ticker", side_effect=Exception("error yf"))
def test_get_last_close_excepcion(mock_ticker, capsys):
    indicator = ShellerPEIndicator()
    valor = indicator.get_last_close("^SPX")
    assert valor is None
    captured = capsys.readouterr()
    assert "Error al obtener el ultimo cierre" in captured.out

# --- fetch_data: downloads and process ---
def test_fetch_data_downloads_and_processes(indicator, mock_yf):
    """Prueba que fetch_data() llama a process_data() y calcula el CAPE diario."""
    # Mockear process_data y get_last_close para evitar dependencias externas
    with patch.object(indicator, 'process_data') as mock_process:
        with patch.object(indicator, 'get_last_close', return_value=4800.0):
            def mock_process_side_effect(filepath):
                indicator.cape_average = 30.0 # Simular el cálculo interno de process_data
            mock_process.side_effect = mock_process_side_effect

            indicator.fetch_data()

            # Verificar que process_data fue llamado con la ruta devuelta por download_latest_file
            mock_process.assert_called_once_with(TEST_FILE_PATH)

            mock_process.assert_called_once() # Ya verificado arriba
            # Si cape_average se asigna, daily_cape debería calcularse
            assert indicator.daily_cape is not None
            assert isinstance(indicator.daily_cape, float)
            expected_daily_cape = 4800.0 / 30.0
            assert indicator.daily_cape == pytest.approx(expected_daily_cape, abs=0.01)

def test_get_last_close_returns_correct_value(indicator):
    """Prueba que get_last_close() devuelve el último cierre del S&P 500."""
    # Mockear yfinance.Ticker
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame({'Close': [4800.0]}, index=pd.to_datetime(['2025-11-17']))
        mock_ticker.return_value = mock_instance

        last_close = indicator.get_last_close("^SPX")
        assert last_close == 4800.0

# --- Nuevas pruebas para normalize() ---

@pytest.fixture
def indicator_with_fixed_stats():
    """Fixture para crear una instancia de ShellerPEIndicator con estadísticas fijas."""
    with patch('indicators.shillerPEIndicator.download_latest_file', return_value=TEST_FILE_PATH):
        indicator = ShellerPEIndicator()
        indicator.promedio_cape_30 = 25.0  # μ
        indicator.desv_cape_30 = 5.0      # σ
        # No inicializamos daily_cape aquí, lo haremos en cada test
        yield indicator

def test_normalize_score_equals_one_when_cape_equals_mean(indicator_with_fixed_stats):
    """Prueba que normalize() devuelve 1 cuando daily_cape = promedio_cape_30."""
    # Configurar valores: daily_cape = μ
    indicator_with_fixed_stats.daily_cape = indicator_with_fixed_stats.promedio_cape_30 # 25.0
    expected_score = 1.0

    score = indicator_with_fixed_stats.normalize()
    assert score == pytest.approx(expected_score, abs=0.01)


def test_normalize_score_approx_075_when_cape_mean_plus_sigma(indicator_with_fixed_stats):
    """Prueba que normalize() devuelve ~0.75 cuando daily_cape = μ + σ."""
    indicator_with_fixed_stats.daily_cape = indicator_with_fixed_stats.promedio_cape_30 + indicator_with_fixed_stats.desv_cape_30 # 30.0

    expected_score = 0.75

    score = indicator_with_fixed_stats.normalize()
    assert score == pytest.approx(expected_score, abs=0.01)

def test_normalize_score_approx_050_when_cape_mean_plus_2sigma(indicator_with_fixed_stats):
    """Prueba que normalize() devuelve ~0.50 cuando daily_cape = μ + 2σ."""
    indicator_with_fixed_stats.daily_cape = indicator_with_fixed_stats.promedio_cape_30 + 2 * indicator_with_fixed_stats.desv_cape_30 # 35.0
    expected_score = 0.50

    score = indicator_with_fixed_stats.normalize()
    assert score == pytest.approx(expected_score, abs=0.01)

def test_normalize_score_equals_zero_when_cape_mean_plus_4sigma(indicator_with_fixed_stats):
    """Prueba que normalize() devuelve 0 cuando daily_cape = μ + 4σ."""
    indicator_with_fixed_stats.daily_cape = indicator_with_fixed_stats.promedio_cape_30 + 4 * indicator_with_fixed_stats.desv_cape_30 # 45.0
    expected_score = 0.0

    score = indicator_with_fixed_stats.normalize()
    assert score == pytest.approx(expected_score, abs=0.01)

def test_normalize_score_equals_one_when_desviation_low(indicator_with_fixed_stats):
    """Prueba que normalize() devuelve 1 cuando desv_cape_30 <= 0.1."""
    # Configurar valores: desv_cape_30 <= 0.1
    indicator_with_fixed_stats.promedio_cape_30 = 25.0
    indicator_with_fixed_stats.desv_cape_30 = 0.1 # Valor límite
    indicator_with_fixed_stats.daily_cape = 30.0 # Cualquier valor debería dar 1 en este caso

    expected_score = 1.0

    score = indicator_with_fixed_stats.normalize()
    assert score == pytest.approx(expected_score, abs=0.01)

def test_normalize_handles_none_values_gracefully(indicator_with_fixed_stats):
    """Prueba que normalize() maneja valores None o no numéricos de forma segura."""
    # Configurar valores que podrían causar problemas
    indicator_with_fixed_stats.promedio_cape_30 = None
    indicator_with_fixed_stats.desv_cape_30 = 5.0
    indicator_with_fixed_stats.daily_cape = 25.0

    score = indicator_with_fixed_stats.normalize()

    assert score is None

    # Reiniciar para el siguiente sub-test
    indicator_with_fixed_stats.__init__() # Reiniciar atributos
    indicator_with_fixed_stats.promedio_cape_30 = 25.0
    indicator_with_fixed_stats.desv_cape_30 = None
    score = indicator_with_fixed_stats.normalize()
    assert score is None

    # Reiniciar para el siguiente sub-test
    indicator_with_fixed_stats.__init__() # Reiniciar atributos
    indicator_with_fixed_stats.desv_cape_30 = 5.0
    indicator_with_fixed_stats.daily_cape = None
    score = indicator_with_fixed_stats.normalize()
    assert score is None

# --- Pruebas para process_data() (opcionales)
def test_process_data_handles_empty_column(tmp_path):
    """Prueba que process_data() maneja correctamente una columna vacía o con solo NaN."""
    # Crear un archivo Excel temporal con una columna vacía
    df = pd.DataFrame({'CAPE': [None, None, None]})
    temp_file = tmp_path / "test_empty.xlsx"
    df.to_excel(temp_file, sheet_name="Data", index=False)

    indicator = ShellerPEIndicator()
    indicator.process_data(str(temp_file))

    # Verificar que los atributos se asignen a None
    assert indicator.cape_average is None
    assert indicator.promedio_cape_30 is None
    assert indicator.desv_cape_30 is None

