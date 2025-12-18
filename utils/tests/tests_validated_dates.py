import pytest
from datetime import date
from utils.validatedDates import (
    validate_date_iso_format,
    validate_date_not_future,
    validate_date_in_range,
    validate_date_was_valid,
    get_a_validated_date
)

def tests_valida_date_iso_format_valid():
    assert validate_date_iso_format("2025-12-17") is True

def test_validate_date_iso_format_invalid():
    assert validate_date_iso_format("17-12-2025") is False

def test_validate_date_not_future_valid(monkeypatch):
    # Simula que hoy es 2025-12-17
    monkeypatch.setattr("data.market_dates.get_market_today", lambda: date(2025, 12, 17))
    assert validate_date_not_future("2025-12-17") is True

def test_validate_date_not_future_future(monkeypatch):
    monkeypatch.setattr("data.market_dates.get_market_today", lambda: date(2025, 12, 17))
    assert validate_date_not_future("2025-12-18") is False

def test_validate_date_in_range_valid():
    assert validate_date_in_range("1995-01-01") is True

def test_validate_date_in_range_invalid():
    assert validate_date_in_range("1985-01-01") is False

def test_validate_date_was_valid_weekday():
    # 2025-12-17 es miércoles, debería ser hábil
    assert validate_date_was_valid("2025-12-17") is True

def test_validate_date_was_valid_weekend():
    # 2025-12-20 es sábado
    assert validate_date_was_valid("2025-12-20") is False

def test_get_a_validated_date_valid(monkeypatch):
    monkeypatch.setattr("data.market_dates.get_market_today", lambda: date(2025, 12, 17))
    assert get_a_validated_date("2025-12-17") is True

def test_get_a_validated_date_invalid_format():
    assert get_a_validated_date("17-12-2025") is False

def test_get_a_validated_date_future(monkeypatch):
    monkeypatch.setattr("data.market_dates.get_market_today", lambda: date(2025, 12, 17))
    assert get_a_validated_date("2025-12-18") is False

def test_get_a_validated_date_out_of_range():
    assert get_a_validated_date("1985-01-01") is False

def test_get_a_validated_date_weekend():
    assert get_a_validated_date("2025-12-20") is False
