import pytest
from freezegun import freeze_time
from db.db_connection import Database
from data.scorer_backup import ScorerBackup

@pytest.fixture(autouse=True)
def fixed_date():
    # Congela market_now().date() a 2025-09-03
    with freeze_time("2025-09-03"):
        yield

@pytest.fixture
def fake_config(monkeypatch):
    """
    Mock de get_config() con pesos y backtesting predecibles.
    IMPORTANTE: parcheamos el símbolo que usa scorer_backup (no el módulo original).
    """
    cfg = {
        "weights": {"fear_greed": 0.34, "spx": 0.33, "vix": 0.33},
        "backtesting": {"start_date": "2010-01-01", "end_date": "2023-12-31"}
    }
    # Parchea el símbolo importado en data.scorer_backup
    monkeypatch.setattr("data.scorer_backup.get_config", lambda: cfg)
    return cfg

@pytest.fixture
def db_mock(monkeypatch):
    class FakeCursor:
        def __init__(self):
            self.queries = []
            self.rowcount = 1
        def execute(self, q, p=None):
            self.queries.append((q, tuple(p or [])))
        def fetchall(self):
            # Para backup_config() -> RETURNING id, (xmax = 0)
            return [{"id": 42,}]
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    class FakeConn:
        def __init__(self):
            self.cursor_obj = FakeCursor()
            self.closed = False
        def cursor(self, *args, **kwargs):
            return self.cursor_obj
        def commit(self):
            pass
        def rollback(self):
            pass  # stub
        def close(self):
            self.closed = True
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    fake_conn = FakeConn()
    fake_db = Database(connection_factory=lambda: fake_conn)
    # Inyectar el singleton
    monkeypatch.setattr(Database, "_instance", fake_db)
    return fake_db

@pytest.fixture
def scorer(db_mock, fake_config, monkeypatch):
    """
    Instancia ScorerBackup con DB mockeada y reemplaza indicadores por fakes
    para evitar redondeos/normalizaciones con valores inesperados.
    """
    s = ScorerBackup(db=db_mock)

    class FakeFG:
        def fetch_data(self):
            class R:
                value = 42
                description = "fake"
            return R()
        def normalize(self):
            return 0.75

    class FakeSPX:
        sma_period = 50
        def fetch_data(self): return 1234.56
        def normalize(self): return 0.45
        def obtener_ultimo_cierre(self): return 2345.67

    class FakeVIX:
        def fetch_data(self): return 12.34
        def normalize(self): return 0.20

    # Sustituye los indicadores reales por los fakes
    s.fg = FakeFG()
    s.sp = FakeSPX()
    s.vx = FakeVIX()

    return s