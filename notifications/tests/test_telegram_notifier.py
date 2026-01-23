import pytest
import types
import json
import tempfile
import os
from notifications.telegramNotifier import (
    TelegramNotifier,
    valoracion_feargreed,
)

##### Helpers #####

def fg(value, description):
    """Helper para crear objetos 'fingidos' para Fear & Greed (si se necesitan en otros tests)."""
    o = types.SimpleNamespace()
    o.value = value
    o.description = description
    return o

class DummyResp:
    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text

##### Tests para valoracion_feargreed #####

def test_valoracion_devuelve_simbolo_correcto():
    assert "🔴" in valoracion_feargreed({"raw_value": 12, "raw_description": "extreme fear"})
    assert "🟡" in valoracion_feargreed({"raw_value": 45, "raw_description": "fear"})
    assert "🟢" in valoracion_feargreed({"raw_value": 70, "raw_description": "greed"})
    assert "🟢" in valoracion_feargreed({"raw_value": 85, "raw_description": "extreme greed"})

def test_valoracion_redondea_valor():
    s = valoracion_feargreed({"raw_value": 49.6, "raw_description": "greed"})
    assert s.startswith("49 ") # Debería redondear 49.6 a 50
    assert "greed" in s

def test_valoracion_invalida_devuelve_none():
    assert valoracion_feargreed(None) is None
    assert valoracion_feargreed({}) is None # Diccionario vacío
    assert valoracion_feargreed("no es un dict") is None # No es un diccionario

def test_valoracion_descripcion_desconocida():
    s = valoracion_feargreed({"raw_value": 10, "raw_description": "meh"})
    assert '⚪' in s
    assert 'meh' in s

    # Prueba con None
    s2 = valoracion_feargreed({"raw_value": None, "raw_description": "fear"})
    assert '-1 🟡 fear' in s2 

##### Tests para TelegramNotifier.load_market_report y generar_reporte_desde_cache #####

def test_load_market_report_archivo_no_existe():
    notifier = TelegramNotifier(report_file_path="/ruta/inexistente.json")
    with pytest.raises(FileNotFoundError):
        notifier.load_market_report()

def test_load_market_report_archivo_vacio():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
        tmp_file.write("") # Cadena vacia
        tmp_path = tmp_file.name

    try:
        notifier = TelegramNotifier(report_file_path=tmp_path)
        with pytest.raises(ValueError):
            notifier.load_market_report()
    finally:
        os.remove(tmp_path) # Limpia el archivo temporal

def test_load_market_report_json_invalido():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
        tmp_file.write("{ esto no es json valido }") # JSON inválido
        tmp_path = tmp_file.name

    try:
        notifier = TelegramNotifier(report_file_path=tmp_path)
        with pytest.raises(ValueError):
            notifier.load_market_report()
    finally:
        os.remove(tmp_path)

def test_load_market_report_contenido_valido():
    sample_data = {
        "SPXIndicator": {
            "calc_date": "2025-01-22",
            "timestamp": "2026-01-20T16:40:27.274320Z",
            "sma_value": 5593.81,
            "normalized_value": 0.28,
            "last_close": 6086.37
        },
        "FearGreedIndicator": {
            "calc_date": "2025-01-22",
            "timestamp": "2026-01-20T16:40:27.276106Z",
            "raw_value": 41,
            "raw_description": "fear",
            "normalized_value": 0.59
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
        json.dump(sample_data, tmp_file)
        tmp_path = tmp_file.name

    try:
        notifier = TelegramNotifier(report_file_path=tmp_path)
        loaded_data = notifier.load_market_report()
        assert loaded_data == sample_data
    finally:
        os.remove(tmp_path)

def test_generar_reporte_desde_cache_ok():
    sample_data = {
        "SPXIndicator": {
            "calc_date": "2025-01-22",
            "timestamp": "2026-01-20T16:40:27.274320Z",
            "sma_value": 5593.81,
            "normalized_value": 0.28,
            "last_close": 6086.37
        },
        "FearGreedIndicator": {
            "calc_date": "2025-01-22",
            "timestamp": "2026-01-20T16:40:27.276106Z",
            "raw_value": 41,
            "raw_description": "fear",
            "normalized_value": 0.59
        },
        "VixIndicator": {
            "calc_date": "2025-01-22",
            "timestamp": "2026-01-20T16:40:27.510514Z",
            "last_close": 15.1,
            "normalized_value": 0.09
        },
        "ShillerPEIndicator": {
            "calc_date": "2025-01-22",
            "timestamp": "2026-01-20T16:40:27.839970Z",
            "daily_cape": 37.13,
            "cape_average": 163.9,
            "promedio_cape_30": 28.06,
            "dev_cape_30": 6,
            "url": "https://shillerdata.com/",
            "normalized_score": 0.63
        },
        "score_calculator": {
            "value": 44.0,
            "date": "2025-01-22"
        }
    }

    # Crear archivo temporal con los datos
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
        json.dump(sample_data, tmp_file)
        tmp_path = tmp_file.name

    try:
        notifier = TelegramNotifier(report_file_path=tmp_path)
        # Mockear load_market_report para devolver nuestros datos simulados
        report_message = notifier.generar_reporte_desde_cache()

        # Verificar que el mensaje contenga partes clave con los valores simulados
        expected_date_calc = "2025-01-22"
        assert f"<b>📊 Reporte Mercado: </b>{expected_date_calc}\n" in report_message
        expected_time_str = "2026-01-20 10:40:27"
        assert f"🕟 Date: {expected_time_str}" in report_message

        assert "41 🟡 fear" in report_message # Valoración Fear & Greed
        assert "0.28" in report_message # Normalized SMA
        assert "5593.81" in report_message # Raw SMA
        assert "0.09" in report_message # Normalized VIX
        assert "0.63" in report_message # Normalized Shiller PE
        assert "6086.37" in report_message # Last Close SPX
        assert "44.00%" in report_message # Score Final (2 decimales)
    finally:
        os.remove(tmp_path)


def test_generar_reporte_desde_cache_datos_incompletos():
    # Datos simulados incompletos o con valores nulos/NaN
    incomplete_data = {
        "SPXIndicator": {},
        "FearGreedIndicator": {"raw_value": 41, "raw_description": "fear"},
        "VixIndicator": {},
        "ShillerPEIndicator": {},
        "score_calculator": {}
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
        json.dump(incomplete_data, tmp_file)
        tmp_path = tmp_file.name

    try:
        notifier = TelegramNotifier(report_file_path=tmp_path)
        report_message = notifier.generar_reporte_desde_cache()

        # Verificar que los campos faltantes se muestren como N/A o 0.00
        assert "N/A" in report_message
        assert "41 🟡 fear" in report_message
    finally:
        os.remove(tmp_path)

##### Tests para TelegramNotifier.enviar_mensaje (sin cambios) #####

def test_envia_con_env_vars(monkeypatch):
    called = {}
    def fake_getenv(k):
        return {"BOT_TOKEN": "T", "CHAT_ID": "C", "USER_IDENTIFIER": "u"}.get(k)

    def fake_post(url, data):
        called["url"] = url
        called["data"] = data
        return DummyResp(200, "OK")

    notifier = TelegramNotifier(report_file_path="/dummy/path.json", post_fn=fake_post, config_fn=lambda _: None, getenv_fn=fake_getenv)
    ok = notifier.enviar_mensaje("hola")
    assert ok is True
    assert called["url"] == "https://api.telegram.org/botT/sendMessage"
    assert called["data"]["chat_id"] == "C"
    assert called["data"]["text"] == "hola"
    assert called["data"]["parse_mode"] == "HTML"

def test_sin_config_lanza_valueerror():
    def fake_getenv(k): return None
    
    notifier = TelegramNotifier(report_file_path="/dummy/path.json", post_fn=lambda u, d: DummyResp(), config_fn=lambda _: None, getenv_fn=fake_getenv)
    with pytest.raises(ValueError):
        notifier.enviar_mensaje("hola")

def test_error_http_lanza_runtimeerror():
    def fake_getenv(k): return {"BOT_TOKEN": "T", "CHAT_ID": "C", "USER_IDENTIFIER": "u"}.get(k)

    def fake_post(url, data): return DummyResp(500, "Bad")

    notifier = TelegramNotifier(report_file_path="/dummy/path.json", post_fn=fake_post, config_fn=lambda _: None, getenv_fn=fake_getenv)
    with pytest.raises(RuntimeError):
        notifier.enviar_mensaje("hola")
