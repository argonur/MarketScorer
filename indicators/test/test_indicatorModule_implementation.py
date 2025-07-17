# Test parametrizado para probar que todas las clases que hereden de IndicatorModule:
# Se pueden instanciar y tienen todos los metodos requeridos (fetch_data, normalize) y get_score

import pytest
from indicators.IndicatorModule import IndicatorModule
from indicators.dummy import Dummy
# from indicators.otra_clase import OtraClase  # puedes agregar más luego

# Lista de todas las clases que implementan IndicatorModule
IMPLEMENTACIONES = [Dummy]  # Agrega aquí tus futuras clases

@pytest.mark.parametrize("Implementation", IMPLEMENTACIONES)
def test_implementacion_valida(Implementation):
    """Verifica que una implementación cumple con el contrato de IndicatorModule."""
    instance = Implementation()
    
    # 1. La instancia debe ser una subclase de IndicatorModule
    assert isinstance(instance, IndicatorModule)
    
    # 2. Debe tener los métodos requeridos
    assert hasattr(instance, 'fetch_data') and callable(instance.fetch_data)
    assert hasattr(instance, 'normalize') and callable(instance.normalize)