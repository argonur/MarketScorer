# 🧪 Guía de Pruebas para Módulos de Indicadores

Esta guía tiene como objetivo estandarizar la forma en que desarrollamos e implementamos pruebas para clases que heredan de la interfaz `IndicatorModule`.

> 🧩 Usa esta guía como plantilla para crear nuevas clases, implementar pruebas unitarias y verificar que se cumplen los contratos definidos por la interfaz.

---

## 📦 Estructura de archivos recomendada

```powershell
indicators/
├── IndicatorModule.py # Interfaz base (ABC)
├── dummy.py # Clase de referencia
├── tu_nueva_clase.py # (Ejemplo de nueva implementación)

tests/
├── test_interface.py # Valida contrato general
├── test_dummy.py # Tests específicos para Dummy
├── test_interface_implementations.py # Tests genéricos parametrizados
├── test_tu_nueva_clase.py # (Nuevos tests específicos)
```

---

## 🧱 Reglas de implementación

### 🧩 La interfaz `IndicatorModule`

Debe incluir:

- `fetch_data()` → **obligatorio**
- `normalize()` → **obligatorio**
- `get_score()` → **opcional (puede sobrescribirse)**

### 🧪 Las clases hijas deben:

- Implementar todos los métodos abstractos.
- Mantener una estructura de pruebas que valide:
  - Instanciación
  - Métodos definidos
  - Retornos esperados

---

## 🧪 ¿Cómo crear una nueva clase con sus tests?

1. **Crear la clase** en el directorio `indicators/` heredando de `IndicatorModule`.
2. **Escribir un archivo de pruebas** en `tests/test_<nombre>.py`.
3. **Añadir tu clase** a `test_interface_implementations.py` para validación genérica.
4. **Correr `pytest`** para validar que todo está en orden.

```bash
pytest indicators/test/
```

## ✅ Tests que debes incluir por convención

Esto dentro de la clase hija que implementa los metodos abstractos de la interfaz. Por ejemplo con la clase `Dummy`:

1. Instanciación y herencia

```python
def test_instance_creation(self, obj):
    assert isinstance(obj, IndicatorModule)
```

2. Métodos definidos

```python
def test_has_required_methods(self, obj):
    assert callable(obj.fetch_data)
    assert callable(obj.normalize)
    assert callable(obj.get_score)
```

3. Valor de retorno esperado

```python
def test_get_score_returns_string(self, obj):
    result = obj.get_score()
    assert isinstance(result, str)
```

---

## 🧪 Herramientas avanzadas de Pytest

- `pytest.raises`: Verificar que se lanza una excepción

```python
import pytest

def test_invalid_call_raises():
    with pytest.raises(ValueError):
        raise ValueError("Entrada no válida")
```

- `pytest.fail`: Forzar un fallo con mensaje personalizado

```python
def test_forzar_fallo_condicional():
    condicion = False
    if not condicion:
        pytest.fail("Este test falló porque 'condicion' es False.")
```

- `pytest.mark.skipif`: Saltar test si se cumple una condición

```python
import sys
import pytest

@pytest.mark.skipif(sys.platform != "linux", reason="Solo funciona en Linux")
def test_solo_en_linux():
    ...
```

- `pytest.warns`: Verificar que se lanza una advertencia

```python
import warnings
import pytest

def test_warns_correctamente():
    with pytest.warns(UserWarning):
        warnings.warn("Advertencia controlada", UserWarning)
```

---

## Test genérico para validar implementaciones

En `tests/test_interface_implementations.py` puedes registrar todas las clases que deseas verificar:

```python
IMPLEMENTACIONES = [Dummy, TuNuevaClase]

@pytest.mark.parametrize("Implementation", IMPLEMENTACIONES)
def test_implementacion_valida(Implementation):
    instancia = Implementation()
    assert isinstance(instancia, IndicatorModule)
    assert callable(instancia.fetch_data)
    assert callable(instancia.normalize)
    assert callable(instancia.get_score)
```

---

# 🔁 Plantilla rápida de test para nueva clase

```python
import pytest
from indicators.mi_nueva_clase import MiNuevaClase
from indicators.IndicatorModule import IndicatorModule

class TestMiNuevaClase:
    @pytest.fixture
    def obj(self):
        return MiNuevaClase()

    def test_instance(self, obj):
        assert isinstance(obj, IndicatorModule)

    def test_fetch_data(self, obj):
        assert obj.fetch_data() is not None

    def test_normalize(self, obj):
        assert obj.normalize() is not None

    def test_get_score(self, obj):
        score = obj.get_score()
        assert isinstance(score, str)
```
