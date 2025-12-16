# data/market_dates.py
from datetime import datetime, timedelta, time, date
from zoneinfo import ZoneInfo

# Configuración por defecto: NYSE
MARKET_TZ = ZoneInfo("America/New_York")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

try:
    from data import market_calendar as mc
    _HAS_CALENDAR = True
except ImportError:
    _HAS_CALENDAR = False

def market_now(now: datetime | None = None, tz: ZoneInfo = MARKET_TZ) -> datetime:
    """
    Devuelve un datetime 'aware' en la zona del mercado.
    - Si now es None -> usa datetime.now(tz)
    - Si now es 'aware' -> lo convierte a tz del mercado
    - Si now es 'naive'  -> asume que está en tz del mercado y le asigna tz
    """
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)

def is_market_open(now: datetime | None = None, market_open: time = MARKET_OPEN, market_close: time = MARKET_CLOSE, tz: ZoneInfo = MARKET_TZ) -> bool:
    """True si estamos entre la hora de apertura y cierre (incluye ambas). No considera feriados."""
    current = market_now(now, tz)
    if current.weekday() >= 5:  # 5=sábado, 6=domingo
        return False
    return market_open <= current.time() <= market_close

def get_market_today(now: datetime | None = None, tz: ZoneInfo = MARKET_TZ) -> date:
    """Devuelve 'la fecha de hoy' en formato date en la zona horaria del mercado (independiente de cierres)."""
    return market_now(now, tz).date()

def get_last_trading_date(now: datetime | None = None, market_close: time = MARKET_CLOSE, tz: ZoneInfo = MARKET_TZ) -> date:
    """
    Devuelve la fecha (date) del último cierre válido:
    - Si es día hábil y la hora actual es < hora de cierre -> usa el día hábil anterior
    - Si es día hábil y la hora actual es >= hora de cierre -> usa hoy
    - Si es fin de semana -> retrocede hasta el viernes más cercano
    No considera feriados (si 'hoy' no abrió, seguirá devolviendo 'hoy' tras el cierre).
    """
    current = market_now(now, tz)

    # Si es fin de semana, retrocede hasta viernes
    if current.weekday() >= 5:
        back = current
        while back.weekday() >= 5:
            back -= timedelta(days=1)
        return back.date()

    # Día hábil
    if current.time() < market_close:
        # Mercado aún abierto -> retroceder al último día hábil anterior
        candidate = current - timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate -= timedelta(days=1)
        if _HAS_CALENDAR:
            try:
                return mc.get_last_valid_trading_day(candidate)
            except Exception:
                pass
        return candidate.date()
    else:
        # Mercado ya cerró -> hoy es válido
        if _HAS_CALENDAR:
            try:
                return mc.get_last_valid_trading_day(current)
            except Exception:
                pass
        return current.date()

def get_last_trading_close(now: datetime | None = None, market_close: time = MARKET_CLOSE, tz: ZoneInfo = MARKET_TZ) -> datetime:
    """
    Devuelve el datetime 'aware' del último cierre (fecha de get_last_trading_date a las market_close).
    """
    last_date = get_last_trading_date(now, market_close, tz)
    return datetime.combine(last_date, market_close, tz)

def yfinance_window_for_last_close(now: datetime | None = None, market_close: time = MARKET_CLOSE, tz: ZoneInfo = MARKET_TZ) -> tuple[str, str]:
    """
    Devuelve (start_str, end_str) en formato 'YYYY-MM-DD' para pedir a yfinance
    el último día con cierre: [start, end) => end = start + 1 día.
    """
    start_d = get_last_trading_date(now, market_close, tz)
    end_d = start_d + timedelta(days=1)
    return (start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d"))
