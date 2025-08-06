# Documentación Técnica

El propósito de este modulo es centralizar la carga y acceso a la configuración del sistema desde un archivo `config.json` garantizando que se cargue una sola vez durante el ciclo de vida del programa.

# Aspectos clave del modulo

## Modulo: `config_loader`

```python
import json
from pathlib import Path
```

- `json`: Permite la conversión (_parse_) al archivo `config.json` en un diccionario de Python
- `Path` De `pathlib`: Es una forma moderna y mas segura para manejar rutas de archivos (alternativa a `os.path`)

---

### Variables Globales

```python
_GLOBAL_CONFIG = None
_CONFIG_PATH = Path(__file__).parent / 'config.json'
```

- `_GLOBAL_CONFIG`:
  - Guarda el contenido del archivo JSON una vez que se ha cargado
  - Permite cargar el archivo una sola vez (Patrón de diseño `Singleton`), evitando lecturas repetidas del disco mejorando así el rendimiento de la aplicación
- `_CONFIG_PATH`:
  - Determina la ubicación del archivo `config.json` relativo a este script
  - Usar `__file__` garantiza que siempre se resuelva la ruta correctamente, sin importar desde donde se ejecute el script principal.
  - Es lo que permite que cualquier otro modulo del sistema pueda acceder a los valores de configuración

---

### Propósito de `load_config`

```python
def load_config(custom_path=None):
```

- Es la función principal encargada de cargar el archivo config.json
- Permite opcionalmente cargar un archivo de configuración distinto si se pasa una ruta personalizada (`custom_path`)

---

### Validaciones de load_config

```python
    global _GLOBAL_CONFIG
```

- Se declara `global` para modificar la variable definida fuera del ámbito local
- Asegura que el cambio al objeto `_GLOBAL_CONFIG` persista globalmente

```python
    if _GLOBAL_CONFIG is not None:
        return _GLOBAL_CONFIG
```

- Evita recargar el archivo si ya ha sido cargado previamente
- Mejora el rendimiento y consistencia de datos

```python
    path = custom_path or _CONFIG_PATH
```

- Selecciona la ruta personalizada si se proporciona una desde `custom_path` en caso de que no, se utiliza la ruta predeterminada
- Flexible para usar archivos distintos en `testing` o distintos entornos de desarrollo

---

### Bloque principal de carga

```python
    try:
        with open(path, 'r') as file:
            _GLOBAL_CONFIG = json.load(file)
            print(f"✅ Configuración cargada correctamente desde: {path}")
            return _GLOBAL_CONFIG
```

- Abre el archivo JSON en modo lectura (`'r'`)
- Utiliza `json.load()` para convertir el contenido en un diccionario de Python
- Asigna el resultado a `_GLOBAL_CONFIG_` evitando una futura recarga
- Muestra un mensaje de éxito indicando la ruta del archivo de configuración

### Manejo de errores especifico

```python
    except json.JSONDecodeError as e:
        print(f"❌ Error de sintaxis de JSON en {path}: {e}")
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado en: {path}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")
        return {}
```

- `JSONDecodeError`: Si el archivo existe pero su contenido no es valido para un archivo JSON
- `FileNotFundError`: Si el archivo de configuración `config.json` no existe en la ruta indicada
- `Exception`: Captura cualquier otro error que se pueda presentar
- `return {}`: En caso de error devuelve un diccionario vacío
- Garantiza que el modulo que usa `load_config` no reviente con un `NoneType`

---

### Función de acceso: `get_config`

```python
def get_config():
    if _GLOBAL_CONFIG is None:
        load_config()
    return _GLOBAL_CONFIG
```

- Abstracción simple para obtener la configuración sin recargarla
- Solo carga el archivo si aun no se ha hecho
- Ideal para usar en el resto del sistema como importándolo como: `from config.config_loader import get_config`

### Opcional: `APP_CONFIG`

```python
# config/config_loader.py
APP_CONFIG = get_config()
```

- Se define una constante al momento de importar el modulo.
- Permite acceso directo al diccionario con: `from config.config_loader import APP_CONFIG`
- Esto puede provocar carga automática, se ofrece como una alternativa a quienes prefieran importar directamente la configuración

---

## Resumen del Diseño del Modulo

| Decisión                           | Razón                                                                            |
| ---------------------------------- | -------------------------------------------------------------------------------- |
| Uso de `_GLOBAL_CONFIG`            | Evita múltiples lecturas del archivo, reduce I/O, mantiene consistencia.         |
| Manejo explícito de errores        | Ayuda al `debugging` y evita fallas silenciosas.                                 |
| Ruta relativa con `Path(__file__)` | Portabilidad y robustez al resolver la ubicación del archivo.                    |
| `get_config()` como abstracción    | Oculta la lógica de carga del cliente; solo se llama y obtiene la configuración. |
| Soporte para `custom_path`         | Flexibilidad en ambientes o pruebas.                                             |
| `APP_CONFIG` como alias            | Comodidad de acceso directo, aunque es optativo.                                 |
