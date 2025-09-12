import pytest
import pandas as pd
from unittest.mock import MagicMock
from indicators.spxIndicator import SIMBOL, SPXIndicator

# Simulamos una respuesta de yfinance
@pytest.fixture
def mock_yf_client():
    """Mock de cliente yfinance"""
    client = MagicMock()
    # Mock de Ticker y history
    ticker_instance = MagicMock()
    client.Ticker.return_value = ticker_instance

    return client, ticker_instance

##### fetch_data #####

def test_fetch_data_ok(mock_yf_client):
    client, ticker_instance = mock_yf_client
    # Simular datos históricos válidos
    data = pd.DataFrame({'Close': [100 + i for i in range(300)]})
    ticker_instance.history.return_value = data

    indicador = SPXIndicator(sma_period=5, upper_ratio= 0.2, lower_ratio=-0.2 , yf_client=client)
    result = indicador.fetch_data()

    assert isinstance(result, float)
    assert result == data['Close'].tail(5).mean()

# Caso fetch_data, vacio

def test_fetch_data_vacio(mock_yf_client, capsys):
    client, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame()
    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)

    indicador.fetch_data()
    captured = capsys.readouterr()
    assert "No se obtuvieron" in captured.out

# Caso fetch_data no obtuvo valores suficientes para SMA

def test_fetch_data_insuficiente_devuelve_none(mock_yf_client):
    client, ticker_instance = mock_yf_client
    data = pd.DataFrame({'Close': [100, 101]}) # Solo 2 dias
    ticker_instance.history.return_value = data
    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)

    with pytest.raises(ValueError, match="dias disponibles"):
        indicador.fetch_data()

def test_fetch_data_columna_close_no_existe(mock_yf_client, capsys):
    client, ticker_instance = mock_yf_client
    
    # DataFrame sin columna 'Close'
    historical_data = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [95, 96, 97],
        'Volume': [1000, 1100, 1200]
    })
    
    ticker_instance.history.return_value = historical_data
    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)

    indicador.fetch_data()
    captured = capsys.readouterr()
    assert "No se obtuvieron" in captured.out

#### Metodo obtener_ultimo_cierre ####

# Caso obtener_ultimo_cierre, valido

def test_obtener_ultimo_cierre_valido(mock_yf_client):
    client, ticker_instance = mock_yf_client
    data = pd.DataFrame({'Close': [200]})
    ticker_instance.history.return_value = data

    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)
    assert indicador.get_last_close(SIMBOL) == 200

# Caso obtener_ultimo_cierre, vacio

def test_obtener_ultimo_cierre_vacio(mock_yf_client):
    client, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame()
    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)

    assert indicador.get_last_close(SIMBOL) is None

def test_obtener_ultimo_cierre_Nulo(mock_yf_client):
    client, ticker_instance = mock_yf_client
    # Hacer que se lance una excepción cuando se llame a history()
    ticker_instance.history.side_effect = Exception("Error:")
    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)

    with pytest.raises(Exception, match="Error:"):
        indicador.get_last_close(SIMBOL)

#### Metodo normalize ####

def test_normalize_limte_inferior(mock_yf_client):
    client, ticker_instance = mock_yf_client
    ticker_instance.history.side_effect = [
        pd.DataFrame({'Close': [100]* 300}), # fetch_data simulado
        pd.DataFrame({'Close': [80]})        # ultimo_cierre
    ]
    indicador = SPXIndicator(sma_period=5, upper_ratio=.02, lower_ratio=-0.2, yf_client=client)

    assert indicador.normalize() == 1.0

def test_normalize_limite_superior(mock_yf_client):
    client, ticker_instance = mock_yf_client
    ticker_instance.history.side_effect = [
        pd.DataFrame({'Close': [100]* 300}),  # fetch_data
        pd.DataFrame({'Close': [120]})        # ultimo_cierre
    ]
    indicador = SPXIndicator(sma_period=5, upper_ratio=.02, lower_ratio=-0.2, yf_client=client)

    assert indicador.normalize() == 0.0

def test_normalize_missing_sma(mock_yf_client, capsys):
    client, ticker_instance = mock_yf_client
    ticker_instance.history.return_value = pd.DataFrame()

    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)
    with pytest.raises(ValueError, match="No se pudo calcular"):
        indicador.normalize()

def test_normalize_missing_last_close(mock_yf_client):
    client, ticker_instance = mock_yf_client
    ticker_instance.history.side_effect = [
        pd.DataFrame({'Close': [100]*300}),
        pd.DataFrame()
    ]

    indicador = SPXIndicator(sma_period=5, upper_ratio=0.2, lower_ratio=-0.2, yf_client=client)
    with pytest.raises(ValueError):
        indicador.normalize()

# test fallido pero valido

def test_normalize_middle_value(mock_yf_client):
    client, ticker_instance = mock_yf_client

    # Simular histórico para SMA y luego último cierre
    # Aseguramos que el ratio sea 0.05 (entre -0.2 y 0.2)
    ticker_instance.history.side_effect = [
        pd.DataFrame({'Close': [100]*300}),  # histórico para SMA
        pd.DataFrame({'Close': [105]})       # último cierre
    ]

    indicador = SPXIndicator(
        sma_period=5,
        upper_ratio=0.2,
        lower_ratio=-0.2,
        yf_client=client
    )

    result = indicador.normalize()

    assert 0.0 < result < 1.0