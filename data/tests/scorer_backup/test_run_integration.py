import pytest

def test_run_success(scorer, db_mock, monkeypatch):
    # 1️⃣ Forzamos valores de retorno
    monkeypatch.setattr(scorer, "backup_config", lambda: 42)
    monkeypatch.setattr(scorer, "backup_fear_greed", lambda cfg_id: None)
    monkeypatch.setattr(scorer, "backup_spx", lambda cfg_id: None)
    monkeypatch.setattr(scorer, "backup_vix", lambda cfg_id: None)
    monkeypatch.setattr(scorer, "backup_score", lambda cfg_id: 88.8)

    # 2️⃣ Ejecutamos run()
    result = scorer.run()

    # 3️⃣ Validamos el resultado
    assert result["date"].isoformat() == "2025-09-02"
    assert result["config_id"] == 42
    assert result["score"] == 88.8

    # 4️⃣ Verificamos que se abrió una transacción
    conn = db_mock.get_connection()
    assert conn.closed is False
    
def test_run_failed(scorer, db_mock, monkeypatch):
    # Simular que backup_spx es quien falla y entonces se lanza la excepcion de run()
    monkeypatch.setattr(scorer, "backup_config", lambda: 42)
    monkeypatch.setattr(scorer, "backup_fear_greed", lambda cfg_id: None)
    # Lanzar Exception con mensaje "DB Error"
    monkeypatch.setattr(scorer, "backup_spx", lambda cfg_id: (_ for _ in ()).throw(Exception("DB Error")))
    monkeypatch.setattr(scorer, "backup_vix", lambda cfg_id: None )
    monkeypatch.setattr(scorer, "backup_score", lambda cfg_id: 88.8)

    with pytest.raises(Exception) as exc:
        scorer.run()
    assert "DB Error" in str(exc.value)