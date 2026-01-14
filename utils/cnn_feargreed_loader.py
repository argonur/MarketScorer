import os, json, requests, datetime
from pathlib import Path
from typing import Optional, Union

CACHE_FILE = Path("data/feargreed.json")
URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

class FearGreedRecord:
    def __init__(self, value: int, description: str, date: datetime.date):
        self.value = value
        self.description = description
        self.date = date

def load_data(force_refresh=False) -> dict:
    """Descarga o carga desde cache el JSON completo del endpoint CNN."""
    if CACHE_FILE.exists() and not force_refresh:
        mtime = datetime.date.fromtimestamp(CACHE_FILE.stat().st_mtime)
        if mtime == datetime.date.today():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    
    # Headers para simular un navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://money.cnn.com/data/fear-and-greed/",
        "Origin": "https://money.cnn.com",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }
    
    try:
        resp = requests.get(URL, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
        return data
    except Exception as e:
        # Si falla la descarga pero existe el caché, usamos el caché
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        # Si no hay caché y falla, registramos el error pero no rompemos
        print(f"Error crítico al obtener datos de CNN Fear & Greed: {str(e)}")
        return None

def get_value_by_date(date: Union[datetime.date, str]) -> Optional[FearGreedRecord]:
    """Devuelve un objeto FearGreedRecord con valor, descripción y fecha."""
    try:
        # Convertir a objeto date si es una cadena
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        elif not isinstance(date, datetime.date):
            raise TypeError("La fecha debe ser un objeto date o una cadena en formato 'YYYY-MM-DD'")
        
        data = load_data()
        if data is None:
            return None
            
        records = data["fear_and_greed_historical"]["data"]
        
        # Buscar la fila que coincide con la fecha
        for rec in records:
            rec_date = datetime.datetime.utcfromtimestamp(rec["x"] / 1000).date()
            if rec_date == date:
                return FearGreedRecord(
                    value=int(rec["y"]),
                    description=rec.get("rating", ""),
                    date=rec_date
                )
        
        # Si no se encuentra exactamente, buscar la fecha más cercana
        closest_record = None
        min_diff = float('inf')
        
        for rec in records:
            rec_date = datetime.datetime.utcfromtimestamp(rec["x"] / 1000).date()
            diff = abs((rec_date - date).days)
            if diff < min_diff:
                min_diff = diff
                closest_record = rec
        
        if closest_record:
            rec_date = datetime.datetime.utcfromtimestamp(closest_record["x"] / 1000).date()
            return FearGreedRecord(
                value=int(closest_record["y"]),
                description=closest_record.get("rating", ""),
                date=rec_date
            )
        
        return None
    except Exception as e:
        print(f"Error al obtener valor por fecha: {e}")
        return None