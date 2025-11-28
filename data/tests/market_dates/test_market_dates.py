import pytest
from zoneinfo import ZoneInfo
from datetime import date, datetime,time, timedelta
from data.market_dates import  market_now, is_market_open, get_last_trading_close, yfinance_window_for_last_close, get_market_today, get_last_trading_date

@pytest.fixture
def ny_tz():
    """ Fixture para la zona horaria de Nueva York (NYSE). """
    return ZoneInfo("America/New_York")

@pytest.fixture
def market_hours():
    """ Fixture para definir el horario de apertura y cierre del mercado. """
    return {
        "open": time(9,30),
        "close": time(16,0)
    }

##### Test para market_now #####
def test_market_now_none_aware(ny_tz):
    resultado = market_now(tz=ny_tz)
    assert resultado.tzinfo == ny_tz

def test_market_now_naive(ny_tz):
    naive_date = datetime(2025, 8, 29, 10, 0)
    resultado = market_now(now=naive_date, tz=ny_tz)
    assert resultado.tzinfo == ny_tz
    assert resultado.hour == 10

def test_market_now_aware_conversion():
    tz_utc = ZoneInfo("UTC")
    aware_dt = datetime(2025, 8, 29, 14, 0, tzinfo=tz_utc)
    result = market_now(now=aware_dt)
    assert result.tzinfo == ZoneInfo("America/New_York")

##### Tests para is_market_open #####
def test_is_market_open_vaido(ny_tz, market_hours):
    # Simulamos un momento dentro del horario de mercado
    now = datetime(2025, 8, 29, 10, 0, tzinfo=ny_tz)
    assert is_market_open(now=now, tz=ny_tz, market_open=market_hours["open"], market_close=market_hours["close"]) is True

def test_is_market_open_mercado_cerrado(ny_tz, market_hours):
    now = datetime(2025, 8, 30, 18, 0, tzinfo=ny_tz)
    assert is_market_open(now=now, tz=ny_tz, market_open=market_hours["open"], market_close=market_hours["close"]) is False

def test_is_market_open_mercado_aun_no_abre(ny_tz, market_hours):
    now = datetime(2025, 8, 29, 7, 0, tzinfo=ny_tz)
    assert is_market_open(now=now, tz=ny_tz, market_open=market_hours["open"], market_close=market_hours["close"]) is False

##### Tests para get_last_trading_close #####
def test_get_last_trading_close_valido(ny_tz, market_hours):
    now = datetime(2025, 8, 29, 17, 0, tzinfo=ny_tz) # Esto es hoy viernes despues del cierre
    close = get_last_trading_close(now=now, tz=ny_tz, market_close=market_hours["close"])
    assert close.weekday() == 4 # Viernes
    assert close.time() == market_hours["close"]

def test_get_last_trading_close_en_fin_de_semana(ny_tz, market_hours):
    now = datetime(2025, 8, 31, 11, 0, tzinfo=ny_tz) # Esto es hoy viernes despues del cierre
    close = get_last_trading_close(now=now, tz=ny_tz, market_close=market_hours["close"])
    assert close.weekday() == 4 # Viernes
    assert close.time() == market_hours["close"]

##### Tests para get_market_today #####
def test_get_market_today(ny_tz):
    now = datetime(2025, 8, 29)
    today = get_market_today(now=now, tz=ny_tz)
    assert today == date(2025,8,29)

##### Tests para get_last_trading_date #####
def test_get_last_trading_date_vuelve_al_viernes(ny_tz, market_hours):
    # Se simula un sabado
    now = datetime(2025,8,30, 12,0, tzinfo=ny_tz)
    last_date = get_last_trading_date(now=now, market_close=market_hours["close"], tz=ny_tz)
    assert last_date.weekday() == 4 # 4 = Viernes

def test_get_last_trading_date_before_close(ny_tz, market_hours):
    now = datetime(2025, 8, 29, 15, 0, tzinfo=ny_tz)  # Viernes antes del cierre
    last_date = get_last_trading_date(now=now, market_close=market_hours["close"], tz=ny_tz)
    assert last_date.weekday() == 4  # Jueves

def test_get_last_trading_date_monday_befote_close(ny_tz, market_hours):
    now = datetime(2025, 9, 1, 15, 0, tzinfo=ny_tz)  # Lunes antes del cierre
    last_date = get_last_trading_date(now=now, market_close=market_hours["close"], tz=ny_tz)
    assert last_date.weekday() == 4  # Viernes

##### Tests para yfinance_window_for_last_close #####
def test_yfinance_window_for_last_close(ny_tz, market_hours):
    now = datetime(2025, 8, 29, 17, 0, tzinfo=ny_tz)  # Viernes después del cierre
    start, end = yfinance_window_for_last_close(now=now, market_close=market_hours["close"], tz=ny_tz)
    assert start == "2025-08-29"
    assert end == "2025-08-30"
