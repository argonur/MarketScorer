import pytest
import json
import os
from pathlib import Path
import config.config_loader as config_loader

##### Auxiliares en la creación y destrucción de archivo de pruebas temporal ####

@pytest.fixture(autouse=True)
def reset_config():
    # Resetear la configuración global antes de cada prueba
    config_loader._GLOBAL_CONFIG = None
    
    yield
    
    # Limpiar archivos después de la prueba
    temp_files = ["test_config.json", "cache_test.json", "invalid.json"]
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)

def create_config_file(content, filename="test_config.json"):
    """ Auxiliar para crear archivos de configuración temporal. """
    with open(filename, 'w') as file:
        json.dump(content, file)
    return filename

#### Pruebas de config_loader ####

def test_valid_config_load(capsys):
    """ Prueba para carga exitosa del archivo JSON. """
    # Crear archivo JSON válido
    config_data = {"appName": "TestApp", "debug": True}
    config_file = create_config_file(config_data, "data/temp/valid_config.json")
    
    # Cargar configuración con ruta personalizada
    result = config_loader.load_config(custom_path=Path(config_file))
    
    # Verificar resultados
    assert result == config_data
    captured = capsys.readouterr()
    assert f"✅ Configuración cargada correctamente desde: {config_file}" in captured.out

def test_config_caching(capsys):
    """ Prueba que la configuración se cachea correctamente """
    # Crear archivo inicial
    config_data1 = {"key": "value1"}
    config_file = create_config_file(config_data1, "cache_test.json")
    
    # Primera carga
    result1 = config_loader.load_config(custom_path=Path(config_file))
    
    # Modificar el archivo
    config_data2 = {"key": "value2"}
    create_config_file(config_data2, "cache_test.json")
    
    # Segunda carga (debería usar caché)
    result2 = config_loader.load_config(custom_path=Path(config_file))
    
    # Verificar que se usó la caché
    assert result1 == config_data1
    assert result2 == config_data1  # Debe ser el mismo que la primera carga
    assert result2 != config_data2  # No debe cargar los nuevos datos
    
    # Verificar mensaje de carga (solo una vez)
    captured = capsys.readouterr()
    assert captured.out.count("✅ Configuración cargada correctamente desde:") == 1

def test_missing_file(capsys):
    """ Prueba cuando el archivo no existe """
    # Intentar cargar archivo inexistente
    result = config_loader.load_config(custom_path=Path("missing_file.json"))
    
    # Verificar resultados
    assert result == {}
    captured = capsys.readouterr()
    assert "❌ Archivo no encontrado en: missing_file.json" in captured.out

def test_invalid_json(capsys):
    """ Prueba con JSON inválido """
    # Crear archivo con JSON inválido
    with open("invalid.json", "w") as f:
        f.write('{"key": "value", "invalid": true,}')  # JSON mal formado
    
    # Cargar archivo inválido
    result = config_loader.load_config(custom_path=Path("invalid.json"))
    
    # Verificar resultados
    assert result == {}
    captured = capsys.readouterr()
    assert "❌ Error de sintaxis de JSON en invalid.json" in captured.out

def test_get_config_function(capsys):
    """ Prueba la función get_config() """
    # Resetear configuración
    config_loader._GLOBAL_CONFIG = None
    
    # Crear archivo temporal
    config_data = {"global": "test"}
    config_file = create_config_file(config_data, "data/temp/global_config.json")
    
    # Parchear la ruta global
    original_path = config_loader._CONFIG_PATH
    config_loader._CONFIG_PATH = Path(config_file)
    
    # Obtener configuración
    result = config_loader.get_config()
    
    # Restaurar ruta original
    config_loader._CONFIG_PATH = original_path
    
    # Verificar resultados
    assert result == config_data
    captured = capsys.readouterr()
    assert f"✅ Configuración cargada correctamente desde: {config_file}" in captured.out