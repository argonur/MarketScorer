import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from indicators.shillerPEIndicator import ShellerPEIndicator, MAX_VALUE

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
