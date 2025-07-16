# Estructura de la clase hija dummy

Se compone por lo siguiente:

1. Importa el paquete IndicatorModule como `from IndicatorModule import IndicatorModule`
2. Hereda de la interfaz `IndicatorModule`

# Estructura del test para el Dummy

1. Como el directorio de los tests se encuentra al mismo nivel que los modulos (`/indicators/`) se debe especificar la ruta del paquete junto al Modulo, Clase o Interfaz.

```python
from indicators.dummy import Dummy
from indicators.IndicatorModule import IndicatorModule
```

2. Nos ayudamos de nuestro archivo de configuracion de tests `conftests.py` que detecta fixtures compartidos por `pytest` sin necesidad de importalos manualmente en cada archivo de test.

- Se definio la fixture en _conftest.py_:

```python
@pytest.fixture(params=[Dummy]) # Agregar los futuros modulos junto a Dummy separados por comas
def indicator_instance():
    return Dummy()
```

Que actúa como una instancia genérica de una clase que implementa la interfaz IndicatorModule.

- Luego nuestro test de la interfaz IndicatorModule la implementa:

```python
@pytest.fixture
def implementation(self, indicator_instance):
    return indicator_instance
```

Esto hace que implementation esté desacoplado de una clase concreta (Dummy), y te permite en el futuro parametrizar esta fixture para testear muchas implementaciones sin reescribir nada.

3. Por ultimo de definen las pruebas para el dummy

```python
    def test_fetch_data_implementation(self, dummy):
        assert dummy.fetch_data() is None

    def test_normalize_implementation(self, dummy):
        assert dummy.normalize() is None

    def test_optional_method_override(self, dummy):
        assert dummy.get_score() == "Dummy sobrescrito"

    def test_instance_creation(self, dummy):
        assert isinstance(dummy, IndicatorModule)

    # Se definiran mas pruebas a futuro que podran servir como plantillas para indicadores reales
```
