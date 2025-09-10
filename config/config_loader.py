import json
from pathlib import Path

# Variable global que almacena la información de config.json
_GLOBAL_CONFIG = None
_CONFIG_PATH = Path(__file__).parent / 'config.json'

def load_config(custom_path=None):
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is not None:
        return _GLOBAL_CONFIG

    path = custom_path or _CONFIG_PATH
    
    try:
        with open(path, 'r') as file:
            _GLOBAL_CONFIG = json.load(file)
            print(f"✅ Configuración cargada correctamente desde: {path}")
            return _GLOBAL_CONFIG
    except json.JSONDecodeError as e:
        print(f"❌ Error de sintaxis de JSON en {path}: {e}")
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado en: {path}")
    return {}

# Cargar configuración solo cuando se solicite explícitamente
def get_config():
    if _GLOBAL_CONFIG is None:
        load_config()
    return _GLOBAL_CONFIG

# Opcional: mantener APP_CONFIG para compatibilidad y acceso directo al importar el modulo
# APP_CONFIG = get_config()