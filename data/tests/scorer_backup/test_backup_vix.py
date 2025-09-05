import logging
import pytest
from psycopg2 import DatabaseError

def test_backup_vix_inserted(scorer, db_mock):
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 1
    scorer.backup_vix(cfg_id=10)
    q, params = cursor.queries[-1]
    assert "INSERT INTO vix_backup" in q
    assert isinstance(params[1], float)
    assert isinstance(params[2], float)

def test_backup_fix_not_inserted(scorer, db_mock, caplog):
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 0
    caplog.set_level(logging.WARNING)
    scorer.backup_vix(cfg_id=44)
    assert "[backup_vix]:" in caplog.text

def test_backup_vix_failed(scorer, db_mock, monkeypatch):
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "execute", lambda *a, **k: (_ for _ in ()).throw(DatabaseError("DB Error")))
    import pytest
    with pytest.raises(RuntimeError) as rte:
        scorer.backup_vix(cfg_id=14)
    assert "Error al respaldar VixIndicator" in str(rte.value)