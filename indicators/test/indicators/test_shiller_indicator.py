from datetime import date
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from indicators.shillerPEIndicator import ShillerPEIndicator

TEST_FILE_PATH = "tests/latest.xlsx"

# ---------- Fixtures ----------
@pytest.fixture
def indicator():
    """Instancia del indicador con download_latest_file mockeado."""
    with patch('indicators.shillerPEIndicator.download_latest_file', return_value=TEST_FILE_PATH):
        yield ShillerPEIndicator()

@pytest.fixture
def mock_yf():
    """Mock de yfinance.Ticker."""
    with patch('yfinance.Ticker', new_callable=MagicMock) as mock_ticker:
        mock_ticker.return_value.history.return_value = pd.DataFrame({'Close': [4800.0]}, index=pd.to_datetime(['2025-11-17']))
        yield mock_ticker

# ---------- Test process_data ----------
def test_process_data_calcula_promedio(tmp_path):
    df = pd.DataFrame({i: range(200) for i in range(11)})
    file_path = tmp_path / "latest.xlsx"
    df.to_excel(file_path, sheet_name="Data", engine="openpyxl", index=False)

    indicator = ShillerPEIndicator()
    indicator._process_data(file_path)

    esperado = pd.Series(range(80, 200)).mean()
    assert pytest.approx(indicator.cape_average, 0.01) == esperado

def test_process_data_menos_valores(tmp_path, capsys):
    df = pd.DataFrame({i: range(3) for i in range(11)})
    file_path = tmp_path / "latest.xlsx"
    df.to_excel(file_path, sheet_name="Data", engine="openpyxl", index=False)

    indicator = ShillerPEIndicator()
    indicator._process_data(file_path)

    captured = capsys.readouterr()
    assert "⚠️ Solo se encontraron" in captured.out
    assert indicator.cape_average == pytest.approx(1.0)

# ---------- Test get_last_close ----------
@patch("indicators.shillerPEIndicator.yf.Ticker")
def test_get_last_close_devuelve_valor(mock_ticker):
    fecha = date(2025, 12, 15)
    mock_df = pd.DataFrame({"Close": [4500.55]})
    mock_ticker.return_value.history.return_value = mock_df

    indicator = ShillerPEIndicator()
    valor = indicator.get_last_close("^SPX", fecha)
    assert valor == 4500.55

@patch("indicators.shillerPEIndicator.yf.Ticker")
def test_get_last_close_empty(mock_ticker, capsys):
    fecha = date(2025, 12, 15)
    mock_ticker.return_value.history.return_value = pd.DataFrame()
    indicator = ShillerPEIndicator()
    valor = indicator.get_last_close("^SPX", fecha)

    assert valor is None
    captured = capsys.readouterr()
    assert "No se pudieron obtener datos" in captured.out

# ---------- Test fetch_data ----------
@patch("indicators.shillerPEIndicator.download_latest_file")
@patch.object(ShillerPEIndicator, "_process_data")
@patch.object(ShillerPEIndicator, "_process_data_30")
@patch.object(ShillerPEIndicator, "get_last_close")
def test_fetch_data_calcula_daily_cape(mock_get_close, mock_process_30, mock_process, mock_download):
    fecha = date(2025, 12, 15)
    mock_download.return_value = "fake.xlsx"
    mock_process.side_effect = lambda filepath: setattr(indicator, "cape_average", 25.0)
    mock_process_30.side_effect = lambda filepath: setattr(indicator, "promedio_cape_30", 20.0) or setattr(indicator, "desv_cape_30", 5.0)
    mock_get_close.return_value = 5000.0

    indicator = ShillerPEIndicator()
    indicator.fetch_data(fecha)
    assert indicator.daily_cape == pytest.approx(200.0)

@patch("indicators.shillerPEIndicator.download_latest_file", return_value=None)
def test_fetch_data_sin_archivo(mock_download):
    fecha = date(2025, 12, 15)
    indicator = ShillerPEIndicator()
    with pytest.raises(RuntimeError):
        indicator.fetch_data(fecha)

@patch("indicators.shillerPEIndicator.download_latest_file", return_value="fake.xlsx")
@patch.object(ShillerPEIndicator, "_process_data", side_effect=Exception("fallo en process_data"))
def test_fetch_data_excepcion_process(mock_process, mock_download):
    fecha = date(2025, 12, 15)
    indicator = ShillerPEIndicator()
    with pytest.raises(Exception):
        indicator.fetch_data(fecha)

def test_fetch_data_downloads_and_processes(indicator, mock_yf):
    fecha = date(2025, 12, 15)
    with patch.object(indicator, '_process_data') as mock_process, \
         patch.object(indicator, '_process_data_30') as mock_process_30, \
         patch.object(indicator, 'get_last_close', return_value=4800.0):

        mock_process.side_effect = lambda filepath: setattr(indicator, "cape_average", 30.0)
        mock_process_30.side_effect = lambda filepath: setattr(indicator, "promedio_cape_30", 25.0) or setattr(indicator, "desv_cape_30", 5.0)

        indicator.fetch_data(fecha)
        mock_process.assert_called_once_with(TEST_FILE_PATH)
        assert indicator.daily_cape == pytest.approx(160.0)

# ---------- Test normalize ----------
@pytest.fixture
def indicator_with_fixed_stats():
    indicator = ShillerPEIndicator()
    indicator.promedio_cape_30 = 25.0
    indicator.desv_cape_30 = 5.0
    yield indicator

def test_normalize_score_equals_one_when_cape_equals_mean(indicator_with_fixed_stats):
    fecha = date(2025, 12, 15)
    indicator_with_fixed_stats.daily_cape = 25.0
    assert indicator_with_fixed_stats.normalize(fecha) == pytest.approx(1.0, abs=0.01)

def test_normalize_score_approx_075_when_cape_mean_plus_sigma(indicator_with_fixed_stats):
    fecha = date(2025, 12, 15)
    indicator_with_fixed_stats.daily_cape = 30.0
    assert indicator_with_fixed_stats.normalize(fecha) == pytest.approx(0.75, abs=0.01)

def test_normalize_score_approx_050_when_cape_mean_plus_2sigma(indicator_with_fixed_stats):
    fecha = date(2025, 12, 15)
    indicator_with_fixed_stats.daily_cape = 35.0
    assert indicator_with_fixed_stats.normalize(fecha) == pytest.approx(0.50, abs=0.01)

def test_normalize_score_equals_zero_when_cape_mean_plus_4sigma(indicator_with_fixed_stats):
    fecha = date(2025, 12, 15)
    indicator_with_fixed_stats.daily_cape = 45.0
    assert indicator_with_fixed_stats.normalize(fecha) == pytest.approx(0.0, abs=0.01)

def test_normalize_score_equals_one_when_desviation_low(indicator_with_fixed_stats):
    fecha = date(2025, 12, 15)
    indicator_with_fixed_stats.promedio_cape_30 = 25.0
    indicator_with_fixed_stats.desv_cape_30 = 0.1
    indicator_with_fixed_stats.daily_cape = 30.0
    assert indicator_with_fixed_stats.normalize(fecha) == pytest.approx(1.0, abs=0.01)

def test_normalize_handles_none_values(indicator_with_fixed_stats):
    fecha = date(2025, 12, 15)
    indicator_with_fixed_stats.promedio_cape_30 = None
    indicator_with_fixed_stats.daily_cape = 25.0
    with pytest.raises(RuntimeError):
        indicator_with_fixed_stats.normalize(fecha)