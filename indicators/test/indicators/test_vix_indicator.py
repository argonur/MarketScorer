import pytest
from unittest.mock import MagicMock
import pandas as pd
from datetime import datetime, timedelta, date
from indicators.vixIndicator import VixIndicator

# Fixture para simular los datos obtenidos de yfinance
@pytest.fixture
def mock_yf_client():
    client = MagicMock()
    ticker_instance = MagicMock()

    # Simulamos los 5 dias habiles con sus valores de cierre
    fechas = [datetime.today() - timedelta(days=i) for i in range(5)]
    fechas = sorted(fechas)
    df_valido = pd.DataFrame({'Close': [14.55, 14.60, 14.65, 14.75, 14.79]}, index=pd.to_datetime(fechas))

    # Por defecto, devuelve datos validos
    ticker_instance.history.return_value = df_valido
    client.Ticker.return_value = ticker_instance

    return client, ticker_instance

######## get_last_close ########
def test_get_last_close_valido(mock_yf_client, start_date="2025-09-12", end_date="2025-09-13", date = "2025-12-15"):
    cliente, _ = mock_yf_client
    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.get_last_close(start_date, end_date, date)
    assert round(resultado, 2) == 14.55

def test_get_last_close_vacio(mock_yf_client, start_date="2025-09-12", end_date="2025-09-13", date="2025-12-15"):
    cliente, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame() # Simulamos que se devuelve una respesta vacia
    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.get_last_close(start_date, end_date, date)
    assert resultado is None

######## fetch_data ########

def test_fetch_data_valido(mock_yf_client, fecha="2025-12-15"):
    cliente, _ = mock_yf_client
    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.fetch_data(fecha)
    assert round(resultado, 2) == 14.55

def test_fetch_data_vacio(mock_yf_client, fecha="2025-12-15"):
    cliente, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame() # Simulamos que se devuelve una respuesta vacia

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.fetch_data(fecha)

    assert resultado is None

######## normalize ########

def test_normalize_valido(mock_yf_client, fecha="2025-12-15"):
    cliente, _ = mock_yf_client
    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.normalize(fecha)

    assert resultado == 0.08

def test_normalize_recibe_None_o_vacio(mock_yf_client, fecha = "2025-12-15"):
    cliente, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame()

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.normalize(fecha)

    assert resultado is None

def test_normalize_limite_inferior():
    fecha = date(2025, 12, 15)
    indicador = VixIndicator(vix_min=9, vix_max=80)
    indicador.fetch_data = lambda d: 6  # Simula un valor por debajo del mínimo

    resultado = indicador.normalize(fecha)
    assert resultado == 0

def test_normalize_limite_superior(fecha = "2025-12-15"):
    indicador = VixIndicator(vix_min=9, vix_max=80)
    indicador.fetch_data = lambda d: 150  # Simula un valor por encima del máximo

    resultado = indicador.normalize(fecha)
    assert resultado == 1

def test_normalize_valor_intermedio(fecha = "2025-12-15"):
    indicador = VixIndicator(vix_min=9, vix_max=80)
    indicador.fetch_data = lambda d: 44.5  # Valor justo en el medio

    resultado = indicador.normalize(fecha)
    assert resultado == 0.5