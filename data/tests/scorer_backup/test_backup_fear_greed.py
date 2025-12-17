import numpy as np
import logging
from psycopg2 import DatabaseError
import pytest

@pytest.fixture
def fake_fg():
    class FakeFG:
        def fetch_data(self, d):
            class R: value = np.float64(10.5); description = "test"
            return R()
        def normalize(self, d): return np.float64(0.75)
    return FakeFG()

def test_backup_fear_greed_insert(scorer, db_mock, fake_fg):
    # Forzamos valores concretos en el indicador
    scorer.fg = fake_fg

    inserted = scorer.db.get_connection().cursor_obj.rowcount = 1
    scorer.backup_fear_greed(cfg_id=1)

    # Verifica parametrización y tipos nativos
    _, params = db_mock.get_connection().cursor_obj.queries[-1]
    assert params[2] == "test"
    #assert isinstance(params[1], float)
    assert isinstance(params[3], float)

def test_backup_fear_greed_no_inserted(caplog, scorer, db_mock, fake_fg):
    scorer.fg = fake_fg
    # Simular rowcount=0 para advertencia
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 0
    caplog.set_level(logging.WARNING)

    scorer.backup_fear_greed(cfg_id=1)
    assert "No se insertaron los registros para" in caplog.text

def test_backup_fear_greed_fails(scorer, db_mock, monkeypatch, fake_fg):
    scorer.fg = fake_fg
    # Simular que cursor.execute se ejecuta
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "execute", lambda *args, **kwargs: (_ for _ in ()).throw(DatabaseError("DB Error")))

    # Esperar a que backup_fear_greed lance la excepcion
    with pytest.raises(RuntimeError) as exc:
        scorer.backup_fear_greed(cfg_id=1)
    assert "Error al respaldar" in str(exc.value)