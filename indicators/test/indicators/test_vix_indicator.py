import pytest
from unittest.mock import MagicMock
import pandas as pd
from datetime import datetime, timedelta
from indicators import vixIndicator
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

######## fetch_data ########

def test_fetch_data_valido(mock_yf_client):
    cliente, _ = mock_yf_client
    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = round(indicador.fetch_data(), 2)

    assert resultado == 14.79

def test_fetch_data_vacio(mock_yf_client):
    cliente, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame() # Simulamos que se devuelve una respuesta vacia

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.fetch_data()

    assert resultado is None

def test_fetch_data_valido_busca_ultimo_cierre(mock_yf_client):
    cliente, ticker_instance = mock_yf_client

    # Simulamos fechas: hoy, ayer, etc.
    fechas = [datetime.today().date() - timedelta(days=i) for i in range(5)]
    fechas = sorted(fechas)

    # Creamos un DataFrame con esos índices
    df_simulado = pd.DataFrame(
        {'Close': [14.15, 14.22, 14.85, 14.97, 15.02]},
        index=pd.to_datetime(fechas)
    )

    # Simulamos que history() devuelve ese DataFrame
    ticker_instance.history.return_value = df_simulado

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = round(indicador.fetch_data(), 2)

    # Si hoy es martes y hay datos para hoy, debería devolver 15.02
    # Si no hay datos para hoy, debería devolver 14.97
    hoy = datetime.today().date()
    if hoy in df_simulado.index.date:
        assert resultado == 15.02
    else:
        assert resultado == 14.97

def test_fetch_data_sin_datos_hoy_usa_ultimo_cierre(mock_yf_client):
    cliente, ticker_instance = mock_yf_client

    # Simulamos fechas que NO incluyen hoy
    fechas = [datetime.today().date() - timedelta(days=i + 1) for i in range(5)]
    fechas = sorted(fechas)

    df_sin_hoy = pd.DataFrame(
        {'Close': [14.15, 14.22, 14.85, 14.97, 15.02]},
        index=pd.to_datetime(fechas)
    )

    ticker_instance.history.return_value = df_sin_hoy

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = round(indicador.fetch_data(), 2)

    # El último cierre anterior a hoy es el más reciente del DataFrame
    assert resultado == 15.02

######## normalize ########

def test_normalize_valido(mock_yf_client):
    cliente, _ = mock_yf_client
    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.normalize()

    assert resultado == 0.08

def test_normalize_recibe_None_o_vacio(mock_yf_client):
    cliente, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame()

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.normalize()

    assert resultado is None

def test_normalize_limite_inferior(mock_yf_client, capsys):
    mensaje = "Fuera de limite inferior"
    cliente, ticker_instance = mock_yf_client

    fechas = [datetime.today() - timedelta(days=i) for i in range(5)]
    fechas = sorted(fechas)
    ticker_instance.history.return_value = pd.DataFrame({'Close': [30, 25, 6, -12, -45]}, index=pd.to_datetime(fechas))

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.normalize()

    out, err = capsys.readouterr()
    assert (mensaje in out) or (mensaje in err)
    assert resultado == 0

def test_normalize_limite_superior(mock_yf_client, capsys):
    mensaje = "Fuera de limite superior"
    cliente, ticker_instance = mock_yf_client

    fechas = [datetime.today() - timedelta(days=i) for i in range(5)]
    fechas = sorted(fechas)
    ticker_instance.history.return_value = pd.DataFrame({'Close': [30, 45, 67, 98, 150]}, index=pd.to_datetime(fechas))

    indicador = VixIndicator(yf_client=cliente, vix_min=9, vix_max=80)
    resultado = indicador.normalize()

    out, err = capsys.readouterr()
    assert (mensaje in out) or (mensaje in err)
    assert resultado == 1