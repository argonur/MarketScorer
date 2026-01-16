import pytest
import datetime
import json
from pathlib import Path
from cnn_feargreed_loader import load_data, get_value_by_date, FearGreedRecord, CACHE_FILE

# --- Fixtures ---
@pytest.fixture
def sample_data():
    return {
        "fear_and_greed_historical": {
            "data": [
                {"x": 1672531200000, "y": 45, "rating": "Neutral"},  # 2023-01-01
                {"x": 1672617600000, "y": 55, "rating": "Greed"},    # 2023-01-02
            ]
        }
    }

@pytest.fixture
def cache_file(tmp_path, sample_data):
    f = tmp_path / "feargreed.json"
    f.write_text(json.dumps(sample_data))
    return f

# --- Tests load_data ---
def test_load_data_from_cache(monkeypatch, cache_file, sample_data):
    monkeypatch.setattr("cnn_feargreed_loader.CACHE_FILE", cache_file)

    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return datetime.date.fromtimestamp(cache_file.stat().st_mtime)

    monkeypatch.setattr("cnn_feargreed_loader.datetime.date", FakeDate)

    data = load_data()
    assert data == sample_data

def test_load_data_download_success(monkeypatch, sample_data, tmp_path):
    def fake_get(*args, **kwargs):
        class Resp:
            def raise_for_status(self): pass
            def json(self): return sample_data
        return Resp()
    monkeypatch.setattr("cnn_feargreed_loader.requests.get", fake_get)
    monkeypatch.setattr("cnn_feargreed_loader.CACHE_FILE", tmp_path / "feargreed.json")
    data = load_data(force_refresh=True)
    assert data == sample_data
    assert (tmp_path / "feargreed.json").exists()

def test_load_data_download_failure_with_cache(monkeypatch, cache_file, sample_data):
    def fake_get(*args, **kwargs): raise Exception("Network error")
    monkeypatch.setattr("cnn_feargreed_loader.requests.get", fake_get)
    monkeypatch.setattr("cnn_feargreed_loader.CACHE_FILE", cache_file)
    data = load_data(force_refresh=True)
    assert data == sample_data

def test_load_data_download_failure_no_cache(monkeypatch, tmp_path):
    def fake_get(*args, **kwargs): raise Exception("Network error")
    monkeypatch.setattr("cnn_feargreed_loader.requests.get", fake_get)
    monkeypatch.setattr("cnn_feargreed_loader.CACHE_FILE", tmp_path / "feargreed.json")
    data = load_data(force_refresh=True)
    assert data is None

# --- Tests get_value_by_date ---
def test_get_value_exact_date(monkeypatch, sample_data):
    monkeypatch.setattr("cnn_feargreed_loader.load_data", lambda *a, **k: sample_data)
    rec = get_value_by_date("2023-01-01")
    assert isinstance(rec, FearGreedRecord)
    assert rec.value == 45
    assert rec.description == "Neutral"
    assert rec.date == datetime.date(2023, 1, 1)

def test_get_value_closest_date(monkeypatch, sample_data):
    monkeypatch.setattr("cnn_feargreed_loader.load_data", lambda *a, **k: sample_data)
    rec = get_value_by_date(datetime.date(2023, 1, 3))  # No existe, debe devolver 2023-01-02
    assert rec.value == 55
    assert rec.description == "Greed"
    assert rec.date == datetime.date(2023, 1, 2)

def test_get_value_invalid_type():
    rec = get_value_by_date(123)
    assert rec is None

def test_get_value_error(monkeypatch):
    monkeypatch.setattr("cnn_feargreed_loader.load_data", lambda *a, **k: None)
    rec = get_value_by_date("2023-01-01")
    assert rec is None