import pytest
from core.scoreCalculator import ScoreCalculator
from psycopg2 import DatabaseError
import logging

def test_backup_score_insert(monkeypatch, scorer, db_mock):
    # Forzamos el score
    monkeypatch.setattr(ScoreCalculator, "get_global_score", staticmethod(lambda: 88.8))
    cursor = db_mock.get_connection().cursor_obj

    # Aseguramos que rowcount sea 1
    cursor.rowcount = 1

    # Llamamos al metodo y esperamos el score devuelto
    resultado = scorer.backup_score(cfg_id=9)
    assert resultado == 88.8

    # Verificamos que se ejecuto el INSERT en el orden de insersion [fecha, score]
    _, params = cursor.queries[-1]
    assert params[0] == scorer.calc_date
    assert params[1] == round(88.8)

def test_backup_no_inserted(caplog, scorer, db_mock, monkeypatch):
    # Forzamos el score
    monkeypatch.setattr(ScoreCalculator, "get_global_score", staticmethod(lambda: 12.3))
    # Simulamos que ya existe el registro
    cursor = db_mock.get_connection().cursor_obj
    cursor.rowcount = 0

    # Capturamos las advertencias
    caplog.set_level(logging.WARNING)
    scorer.backup_score(cfg_id=9)
    assert "No se insertaron los registros para" in caplog.text

def test_backup_score_fails(scorer, db_mock, monkeypatch):
    """
    Forzamos DB error y fijamos score para evitar cálculo real.
    """
    monkeypatch.setattr(ScoreCalculator, "get_global_score", staticmethod(lambda: 77.7))
    cursor = db_mock.get_connection().cursor_obj
    monkeypatch.setattr(cursor, "execute", lambda *args, **kwargs: (_ for _ in ()).throw(DatabaseError("DB Error")))

    with pytest.raises(RuntimeError) as rte:
        scorer.backup_score(cfg_id=8)
    assert "Error al respaldar" in str(rte.value)