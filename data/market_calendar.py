import pandas_market_calendars as mcal
import yfinance as yf
from datetime import datetime, timedelta

nyse = mcal.get_calendar("NYSE")

def get_trading_schedule(start: str, end: str):
    """ Devuelve el calendario oficial de trading (apertura / cierre) entre fechas """
    return nyse.schedule(start_date=start, end_date=end)

def get_last_valid_trading_day(symbol="^SPX", now=None):
    """
        Devuelve el ultimo cierre habil con datos reales.
        - Usa calendario oficial para saber si el dia fue habil
        - Valida contra yfinance para confirmar que hubo datos
    """
    if now is None:
        now = datetime.now()

    # Retroceder hasta encontrar un dia con datos
    while True:
        schedule = nyse.schedule(start_date=now.date().isoformat() , end_date=now.date().isoformat())
        if not schedule.empty:
            datos = yf.Ticker(symbol).history(
                start = now.date().isoformat(), end = (now.date() + timedelta(days=1)).isoformat())
            
            if not datos.empty:
                return now.date()
        now -= timedelta(days=1)