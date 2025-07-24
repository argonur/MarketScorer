El sistema requiere implementar múltiples indicadores financieros (_Fear and Greed, VIX, etc_), que tienen fuentes de distintas (**API, Archivos o DB**).
Entonces para que estas clases sean testeables reutilizables y mantenibles, se ha optado por aplicar `inyección de dependencias` a través del constructor de cada clase que herede de **IndicatorModule**.

### ¿Qué es la inyección de dependencias?

Es un patrón de diseño que consiste en "_pasar las dependencias desde fuera de la clase_", en lugar de que las cree o importe directamente.

- Por ejemplo:

```python
from fear_and_greed import get as get_fear_greed_current
# Importar la clase padre IndicatorModule

class FearGreedIndicator(IndicatorModule):
	def __init__(self, fetch_fn=get_fear_greed_current):
		self.fetch_fn = fetch_fn

	# metodo para obtener el indice
	def fetch_data(self):
		fgi = self.fetch_fn() # Aquí se ejecuta la función inyectada desde el constructor
```

> [!note]
> Aquí `fetch_fn` es un parámetro inyectado, es decir, se le puede pasar desde afuera (por ejemplo, como un mock en tests), pero si no se pasa nada, usa el valor por defecto: `get_fear_greed_current`.

# Beneficios

#### 1. Testabilidad

Permite simular comportamiento en los tests (como errores o respuestas especificas) sin depender de API's reales.

#### 2. Desacoplamiento

La clase no depende directamente de `get_fear_greed_current`, si no de una función que le entregamos. Eso facilita su reutilización.

#### 3. Escalabilidad

Cada nuevo indicador puede recibir su propia fuente de datos, sin repetir estructuras ni depender de lógica externa rígida.

#### 4. Control de entorno

Se puede inyectar una fuente diferente en producción o desarrollo.

---

# ¿Qué son los fixtures?

En `pytest`, los fixtures son funciones que devuelven datos, objetos o comportamientos que vas a usar en los test.
Sirven para:

- Preparar el contexto (_mock data, objetos, DB, etc_)
- Reutilizar código sin repetir setups.

---

# En la practica

Ya definimos que nuestro constructor de clase se define de la siguiente manera:

- Constructor de la clase

```python
 def __init__(self, fetch_fn=get_fear_greed_current):
        """
        Inyección de dependencia:
        - fetch_fn: función externa que retorna el valor del FGI.
        """
        self.fetch_fn = fetch_fn
```

Como siguiente paso, definimos un fixture en un archivo dentro del directorio que contendrá a los tests `/tests/conftests.py `, este fixture será el que contendrá la configuración y estructura para el mock.

```python
# Importamos las librerias
import pytest
from indicators.FearGreedIndicator import FearGreedIndicator
from unittest.mock import MagicMock

@pytest.fixture
def mock_fgi():
	obj = MagicMock()
	obj.value = 70
	obj.description = "Greed"
	obj.last_update = "2025-07-21"
	return obj

@pytest.fixture
def fetch_ok(mock_fgi): #recibe el constructor mock_fgi
	return lambda: mock_fgi

@pytest.fixture
def fetch_error():
	def fn():
		raise Exception("API Caida") # En caso de que no se reciban datos
	return fn

@pytest.fixture
def fetch_none():
	return lambda: None
```

### Explicación detallada de los `fixtures`

##### 1. Fixture -> `mock_fgi`:

```python
@pytest.fixture
def mock_fgi():
    obj = MagicMock()
    obj.value = 70
    obj.description = "Greed"
    obj.last_update = "2025-07-21"
    return obj
```

- Crea un objeto simulado (_MagicMock_) que actúa como si fuera el resultado de la API de `fear_and_greed`.
- Lo usamos en los tests para no depender del API real.

##### 2. Fixture -> `fetch_ok`

```python
@pytest.fixture
def fetch_ok(mock_fgi):
    return lambda: mock_fgi
```

- Simula una **función** que retorna un `mock_fgi`.
- Se comporta como `get_fear_greed_current`, pero controlado por ti.
- Ideal para pruebas donde el indicador funciona bien.

##### 3. Fixture -> `fetch_error`

```python
@pytest.fixture
def fetch_error():
    def fn():
        raise Exception("API caída")
    return fn
```

- Simula una función que lanza un error.
- Útil para probar si tu clase maneja bien excepciones (resiliencia).

##### 4. Fixture -> `fetch_none`

```python
@pytest.fixture
def fetch_none():
    return lambda: None
```

- Simula una función que retorna `None`, como si la API no devolviera datos válidos.
- Útil para verificar cómo responde la clase ante fallos silenciosos.

---

# Test organizados por complejidad

#### 1. Test Básico (casos validos)

En este caso desde nuestro fixture `mock_fgi` donde simulamos los datos, simulamos recibir un valor de _70_ de nuestro metodo `fetch_data()` por lo que este será nuestro valor esperado en el test.

```python
from indicators.fear_greed import FearGreedIndicator

def test_fetch_data_valida(fetch_ok):
    indicador = FearGreedIndicator(fetch_fn=fetch_ok)
    resultado = indicador.fetch_data()
    assert resultado.value == 70   # Valor esperado correcto.

def test_normalize_valido(fetch_ok):
    indicador = FearGreedIndicator(fetch_fn=fetch_ok)
    assert indicador.normalize() == 0.7   # Valor esperado correcto.
```

Entonces `normalize()` recibe el valor de `fetch_data()` y de acuerdo a la formula el valor esperado debe ser _0.7_.

- Ambos valores coinciden, por lo tanto el test **Pasa**

#### 2. Nivel intermedio (Casos `fetch_data` no devuelve ningún valor)

Ya sea por motivos de conexión a internet o de la propia API, debemos ser capaces de manejar errores por falta de información obtenida de la API.

- Manejar el error desde nuestro método `fetch_data()`

```python
# Importar librerias y modulos ...
# Constructor de la clase ...

def fetch_data(self):
    try:
        fgi = self.fetch_fn()
        if not (0 <= fgi.value <= 100):
            raise ValueError(f"Valor fuera de rango esperado: {fgi.value}")
        print(f"Valor actual del CNN Fear & Greed Index: {fgi.value.__round__()} ({fgi.description})")
        print(f"Última actualización: {fgi.last_update}")
        return fgi
    except Exception as e:
        print(f"[ERROR] al obtener el valor actual: {e}")
        return None

```

- Simulando el caso donde la API no obtiene ningún valor, nuestros test para `fetch_data` y `normalize` deben ser capaces de manejarlo.

> [!success] raise ValueError
> Cuando ocurre un `ValueError` por valor fuera de rango, el `fetch_data()` lo atrapa dentro del `try-except` y retorna `None`, por lo tanto `normalize()` no ve el error como excepción sino como "falta de datos", devolviendo 0. Esto permite que el sistema no se interrumpa en producción.

```python
from indicators.fear_greed import FearGreedIndicator

def test_fetch_data_error(fetch_error):
    indicador = FearGreedIndicator(fetch_fn=fetch_error)
    assert indicador.fetch_data() is None

def test_normalize_falla(fetch_none):
    indicador = FearGreedIndicator(fetch_fn=fetch_none)
    assert indicador.normalize() == 0

```

#### 3. Nivel Avanzado (test parametrizados)

Para este tipo de test debemos reconfigurar nuestra estructura de nuestro objeto simulado, para 2 valores.

- valor = valor esperado obtenido por la API.
- esperado = valor resultante después del método `normalize`.

```python
# Valores validos esperados, dentro del rango
@pytest.mark.parametrize("valor, esperado", [
    (75, 0.75),
    (55, 0.55),
    (25, 0.25),
    (20, 0.2),
    (100, 1.0),
    (0, 0.0)
])
def test_normalize_parametrizado(valor, esperado):
    mock_fgi = MagicMock()
    mock_fgi.value = valor
    mock_fgi.description = "mock"
    mock_fgi.last_update = "2025-07-21"

    indicador = FearGreedIndicator(fetch_fn=lambda: mock_fgi)

    assert indicador.normalize() == esperado
```

- _Parametrize_ considerando solo 1 valor:

```python
# Valores invalidos no esperados, fuera de rango
@pytest.mark.parametrize("valor_fuera_de_rango", [-70, -1, -25, 105, 125])
def test_valores_fuera_de_rango_lanza_excepcion(valor_fuera_de_rango):
    class MockFGI:
        def __init__(self, value):
            self.value = value
            self.description = "Test"
            self.last_update = "2025-07-21"

    fetch_mock_exception = lambda: MockFGI(valor_fuera_de_rango)
    indicador = FearGreedIndicator(fetch_fn=fetch_mock_exception)

    # verificamos que se lanza la excepcion al obtener datos fuera de rango

    resultado = indicador.fetch_data()

    assert resultado is None # Porque la excepcion se atrapa dentro de la clase y entonces devuelve un None en el Exception
```

# Buenas practicas

- No relies en llamadas reales a API en tests.
- Usa `pytest.mark.parametrize` para cubrir rangos de valores.
- Testea tanto casos de éxito como fallos posibles.
- Asegura que tus clases manejen valores inesperados con `try-except` o validaciones explícitas.
- Agrega comentarios en fixtures y tests para que nuevos desarrolladores comprendan el propósito.
