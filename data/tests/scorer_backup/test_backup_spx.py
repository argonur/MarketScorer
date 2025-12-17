import logging
import numpy as np
from psycopg2 import DatabaseError
import pytest

# Agregamos un fixture para compartir el falso SPX
@pytest.fixture
def fake_spx():
    class FakeSPX:
        sma_period = 100
        d = "2025-12-12"
        def fetch_data(self, d): return 1234.5678
        def normalize(self, d): return 0.33
        def get_last_close(self, SIMBOL, d): return 2345.6789
    return FakeSPX()


def test_backup_spx_insert(scorer, db_mock, fake_spx):
    scorer.sp = fake_spx
    inserted = scorer.db.get_connection().cursor_obj.rowcount = 1
    scorer.backup_spx(cfg_id=5)
    _, params = db_mock.get_connection().cursor_obj.queries[-1]
    # sma_period tiene que respetarse
    assert params[1] == 100
    assert isinstance(params[2], float)
    assert isinstance(params[3], float)
    assert isinstance(params[4], float)

def test_backup_spx_not_inserted(scorer, db_mock, caplog, fake_spx):
    # Simular rowcount=0 para advertencia
    scorer.sp = fake_spx
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 0
    caplog.set_level(logging.WARNING)
    
    scorer.backup_spx(cfg_id=5)
    assert "No se insertaron los registros para" in caplog.text

def test_backup_spx_failed(scorer, db_mock, caplog, monkeypatch, fake_spx):
    # Simular cursor.execute
    scorer.sp = fake_spx
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "execute", lambda *args, **kwargs: (_ for _ in ()).throw(DatabaseError("DB Error")))

    # Lanzar la excepcion
    with pytest.raises(RuntimeError) as exc:
        scorer.backup_spx(cfg_id=16)
    assert "Error al respaldar" in str(exc.value)