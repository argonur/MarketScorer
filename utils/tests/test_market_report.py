import pytest
import json
import os
from datetime import datetime, timedelta, date
from utils.MarketReport import MarketReport

@pytest.fixture
def temp_file(tmp_path):
    """Fixture para usar un archivo temporal en lugar del real."""
    return tmp_path / "market_report.json"

@pytest.fixture
def report(temp_file):
    """Instancia de MarketReport con archivo temporal."""
    return MarketReport(filepath=str(temp_file))

########## set_data / get_data ##########

def test_set_and_get_data(report):
    report.set_data("spx", 4200, "2025-12-15")
    data = report.get_data("spx")
    assert data["value"] == 4200
    assert data["date"] == "2025-12-15"

def test_set_data_crea_archivo(report, temp_file):
    report.set_data("vix", 15.5, "2025-12-15")
    assert temp_file.exists()
    contenido = json.loads(temp_file.read_text(encoding="utf-8"))
    assert "vix" in contenido

########## set_indicator_data / get_indicator_data ##########

def test_set_and_get_indicator_data(report):
    indicador_data = {"sma_value": 4200.55, "normalized_value": 0.75}
    report.set_indicator_data("SPXIndicator", indicador_data, "2025-12-15")
    data = report.get_indicator_data("SPXIndicator")
    assert data["sma_value"] == 4200.55
    assert data["normalized_value"] == 0.75
    assert data["calc_date"] == "2025-12-15"
    assert "timestamp" in data

########## get_all_data ##########

def test_get_all_data(report):
    report.set_data("vix", 18.2, "2025-12-15")
    report.set_indicator_data("SPXIndicator", {"sma_value": 4200}, "2025-12-15")
    all_data = report.get_all_data()
    assert "vix" in all_data
    assert "SPXIndicator" in all_data

########## clear ##########

def test_clear(report):
    report.set_data("vix", 20, "2025-12-15")
    report.clear()
    assert report.get_all_data() == {}

########## load ##########

def test_load_existing_file(report, temp_file):
    contenido = {"spx": {"value": 4200, "date": "2025-12-15"}}
    temp_file.write_text(json.dumps(contenido), encoding="utf-8")
    nuevo_report = MarketReport(filepath=str(temp_file))
    assert nuevo_report.get_data("spx")["value"] == 4200

def test_load_corrupt_file(temp_file):
    temp_file.write_text("{corrupt-json}", encoding="utf-8")
    report = MarketReport(filepath=str(temp_file))
    assert report.get_all_data() == {}

########## is_up_to_date ##########

def test_is_up_to_date_true(report):
    fecha = (datetime.now() - timedelta(days=1)).isoformat()
    report.set_indicator_data("SPXIndicator", {"sma_value": 4200}, fecha)
    assert report.is_up_to_date("SPXIndicator", max_age_days=2) is True

def test_is_up_to_date_false(report):
    fecha = (datetime.now() - timedelta(days=5)).isoformat()
    report.set_indicator_data("SPXIndicator", {"sma_value": 4200}, fecha)
    assert report.is_up_to_date("SPXIndicator", max_age_days=2) is False

def test_is_up_to_date_invalid_date(report):
    report.set_indicator_data("SPXIndicator", {"sma_value": 4200}, "fecha-invalida")
    assert report.is_up_to_date("SPXIndicator") is False