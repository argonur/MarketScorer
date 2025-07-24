from indicators.dummy import Dummy # Se importa el modulo a instanciar que se retornara
from indicators.FearGreedIndicator import FearGreedIndicator
from unittest.mock import MagicMock
import pytest

@pytest.fixture(params=[
    Dummy,
    lambda: FearGreedIndicator(fetch_fn=lambda: None) #fetch_fn simulado vacio
    ]) # Agregar los futuros modulos junto a Dummy separados por comas
def indicator_instance(request):
    return request.param()

@pytest.fixture
def mock_fgi():
    obj = MagicMock()
    obj.value = 70
    obj.description = "Greed"
    obj.last_update = "2025-07-21"
    return obj

@pytest.fixture
def fetch_ok(mock_fgi):
    return lambda: mock_fgi

@pytest.fixture
def fetch_error():
    def fn():
        raise Exception("API Caida")
    return fn

@pytest.fixture
def fetch_none():
    return lambda: None