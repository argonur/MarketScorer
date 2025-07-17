from indicators.dummy import Dummy # Se importa el modulo a instanciar que se retornara
import pytest

@pytest.fixture(params=[Dummy]) # Agregar los futuros modulos junto a Dummy separados por comas
def indicator_instance():
    return Dummy()
