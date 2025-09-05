import pytest
from psycopg2 import DatabaseError

def test_backup_config_success(scorer, db_mock):
    cfg_id = scorer.backup_config()
    assert cfg_id == 42
    q, params = db_mock.get_connection().cursor_obj.queries[-1]
    assert "INSERT INTO config_backup" in q
    assert params[0] == scorer.calc_date

def test_backup_config_fail_empty(monkeypatch, scorer, db_mock):
    # Simula un fetchall() vacío => IndexError en result[0]
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "fetchall", lambda: [])
    with pytest.raises(IndexError):
        scorer.backup_config()

def test_backup_config_fails(monkeypatch, scorer, db_mock):
    # Simula que cursor.execute lanza DatabaseError
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "execute", lambda *a, **k: (_ for _ in ()).throw(DatabaseError("DB Error")))
    with pytest.raises(RuntimeError) as exc:
        scorer.backup_config()
    assert "Error al respaldar la configuración" in str(exc.value)