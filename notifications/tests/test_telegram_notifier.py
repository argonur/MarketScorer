import pytest
import types
from notifications.telegramNotifier import TelegramNotifier, valoracion_feargreed

##### Test para la valoracion_feargreed() #####
def fg(value, description):
    o = types.SimpleNamespace()
    o.value = value
    o.description = description

    return o

def test_devuelve_simbolo_por_descripcion():
    assert "🔴" in valoracion_feargreed(fg(12.7, "extreme fear"))
    assert "🟡" in valoracion_feargreed(fg(45, "fear"))
    assert "🟢" in valoracion_feargreed(fg(70, "greed"))
    assert "🟢" in valoracion_feargreed(fg(85, "extreme greed"))

def test_redondea_valor_y_normaliza_caso():
    s = valoracion_feargreed(fg(49.6, "Greed"))
    assert s.startswith("50 ")
    assert "greed" in s

def test_invalido_o_devuelve_none():
    assert valoracion_feargreed(None) is None

    # Si faltan atributos esperados
    class Bad: pass
    assert valoracion_feargreed(Bad()) is None

def test_descripcion_desconocida():
    s = valoracion_feargreed(fg(10, "meh"))
    assert '⚪' in s
    assert s.endswith(" meh") or s.endswith(" unknow")

##### Test para enviar mensajes con monkeypatch #####
class DummyResp:
    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text

def test_envia_con_env_vars(monkeypatch):
    called = {}

    def fake_getenv(k):
        return {"BOT_TOKEN": "T", "CHAT_ID": "C", "USER_IDENTIFIER": "u"}.get(k)

    def fake_post(url, data):
        called["url"] = url
        called["data"] = data
        return DummyResp(200, "OK")

    notifier = TelegramNotifier(post_fn=fake_post, config_fn=lambda _: None, getenv_fn=fake_getenv)
    ok = notifier.enviar_mensaje("hola")
    assert ok is True
    assert called["url"] == "https://api.telegram.org/botT/sendMessage"
    assert called["data"]["chat_id"] == "C"
    assert called["data"]["text"] == "hola"
    assert called["data"]["parse_mode"] == "HTML"

def test_fallback_db_config(monkeypatch):
    def fake_getenv(k):
        return {"USER_IDENTIFIER": "user@example.com"}.get(k)

    def fake_config(uid):
        assert uid == "user@example.com"
        return {"BOT_TOKEN": "T2", "CHAT_ID": "C2"}

    notifier = TelegramNotifier(
    post_fn=lambda url, **kwargs: DummyResp(),
    config_fn=fake_config,
    getenv_fn=fake_getenv,
    )
    assert notifier.enviar_mensaje("hola")

def test_sin_config_lanza_valueerror():
    def fake_getenv(k): return None
    notifier = TelegramNotifier(post_fn=lambda u, d: DummyResp(), config_fn=lambda _: None, getenv_fn=fake_getenv)
    with pytest.raises(ValueError):
        notifier.enviar_mensaje("hola")

def test_error_http_lanza_runtimeerror():
    def fake_getenv(k): return {"BOT_TOKEN": "T", "CHAT_ID": "C", "USER_IDENTIFIER": "u"}.get(k)
    def fake_post(url, data): return DummyResp(500, "Bad")
    notifier = TelegramNotifier(post_fn=fake_post, config_fn=lambda _: None, getenv_fn=fake_getenv)
    with pytest.raises(RuntimeError):
        notifier.enviar_mensaje("hola")

##### Test para enviar reporte a la aplicación #####
class FakeFG:
    def __init__(self, value=68, description="greed"):
        self.value = value
        self.description = description
    def fetch_data(self):
        return self  # el propio objeto

class FakeSPX:
    def normalize(self): return 0.73
    def fetch_data(self): return 4567.89
    def obtener_ultimo_cierre(self): return 4550.12

class FakeVix:
    def normalize(self): return 0.08

class FakeScore:
    def __init__(self, indicators, weights): pass
    def calculate_score(self): return 61.7

def test_ensambla_y_envia_mensaje(monkeypatch):
    sent = {}
    def fake_post(url, data):
        sent["url"] = url
        sent["data"] = data
        class R: status_code=200; text="OK"
        return R()
    def fake_getenv(k):
        return {"BOT_TOKEN":"X", "CHAT_ID":"Y", "USER_IDENTIFIER":"u"}.get(k)

    msg = TelegramNotifier.enviar_reporte_mercado(
        post_fn=fake_post,
        config_fn=lambda uid: None,
        getenv_fn=fake_getenv,
        spx_cls=FakeSPX,
        fg_cls=lambda: FakeFG(68, "greed"),
        vix_cls=FakeVix,
        score_cls=FakeScore,
    )

    # Aserciones sobre el mensaje y el payload enviado
    assert msg.startswith("<b>📊 Reporte Mercado</b>")
    assert "CNN Fear & Greed: <b>68 🟢 greed</b>" in msg
    assert "SMA-200 S&P 500: <b>0.73</b>" in msg
    assert "Calculo SMA-200 S&P500: <b>4567.89</b>" in msg
    assert "Valor normalizado de Vix: <br>0.08</br>"
    assert "Último Cierre S&P 500: <b>4550.12</b>" in msg
    assert "Score Final: <b>62%</b>" in msg

    assert sent["url"] == "https://api.telegram.org/botX/sendMessage"
    assert sent["data"]["chat_id"] == "Y"
    assert sent["data"]["text"] == msg
