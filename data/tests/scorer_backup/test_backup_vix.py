import logging
import pytest
from psycopg2 import DatabaseError

@pytest.fixture
def fake_vix():
    class FakeVIX:
        d = "2025-12-12",
        def fetch_data(self, d): return 17.0
        def normalize(self, d): return 0.33
    return FakeVIX()

def test_backup_vix_inserted(scorer, db_mock, fake_vix):
    scorer.vx = fake_vix
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 1
    scorer.backup_vix(cfg_id=10)
    q, params = cursor.queries[-1]
    assert "INSERT INTO vix_backup" in q
    assert isinstance(params[1], float)
    assert isinstance(params[2], float)

def test_backup_fix_not_inserted(scorer, db_mock, caplog, fake_vix):
    scorer.vx = fake_vix
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 0
    caplog.set_level(logging.WARNING)
    scorer.backup_vix(cfg_id=44)
    assert "[backup_vix]:" in caplog.text

def test_backup_vix_failed(scorer, db_mock, monkeypatch, fake_vix):
    scorer.vx = fake_vix
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "execute", lambda *a, **k: (_ for _ in ()).throw(DatabaseError("DB Error")))
    import pytest
    with pytest.raises(RuntimeError) as rte:
        scorer.backup_vix(cfg_id=14)
    assert "Error al respaldar VixIndicator" in str(rte.value)