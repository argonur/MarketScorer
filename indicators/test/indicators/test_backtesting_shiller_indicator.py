import pandas as pd
from datetime import date
import pytest
from indicators.shillerPEIndicator import ShillerPEIndicator

# ---------- Fixtures ----------
@pytest.fixture
def indicator():
    return ShillerPEIndicator()

# ---------- Test parser_shiller_dates_searcher ----------
def test_parser_shiller_dates_searcher_converts_dates(indicator):
    df = pd.DataFrame({
        0: ["2025.09", "2025.10", "2025.11"],
        10: [100, 200, 300],
        12: [400, 500, 600]
    })
    df = indicator.parser_shiller_dates_searcher(df)
    assert "fecha" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"])

# ---------- Test filter_until_date ----------
def test_filter_until_date_filters_correctly(indicator):
    df = pd.DataFrame({
        0: ["2025.09", "2025.10", "2025.11"],
        10: [100, 200, 300]
    })
    df = indicator.parser_shiller_dates_searcher(df)
    target_date = date(2025, 10, 15)
    df_filtrado = indicator.filter_until_date(df, target_date)
    # Ahora debe incluir solo septiembre porque retrocede un mes
    assert len(df_filtrado) == 1
    assert df_filtrado.iloc[0]["fecha"].month == 9

# ---------- Test extract_numeric_column ----------
def test_extract_numeric_column_returns_tail(indicator):
    # Crear DataFrame con 11 columnas, valores en la posición 10
    data = {i: list(range(50)) for i in range(11)}
    df = pd.DataFrame(data)
    values = indicator.extract_numeric_column(df, 10, 5)
    assert list(values) == [45, 46, 47, 48, 49]

def test_extract_numeric_column_handles_nans(indicator):
    data = {i: [1, None, 3, None, 5] for i in range(13)}
    df = pd.DataFrame(data)
    values = indicator.extract_numeric_column(df, 10, 3)
    # El método devuelve los últimos 3 valores no nulos: [1.0, 3.0, 5.0]
    assert list(values) == [1.0, 3.0, 5.0]

# ---------- Test calculate_cape_average ----------
def test_calculate_cape_average_computes_mean(indicator):
    data = {i: [None, None, None] for i in range(11)}
    data[0] = ["2025.09", "2025.10", "2025.11"]
    data[10] = [100, 200, 300]
    df = pd.DataFrame(data)
    target_date = date(2025, 10, 15)
    promedio = indicator.calculate_cape_average(df, target_date, max_value=2)
    assert promedio == pytest.approx(100.0)

# ---------- Test calculate_cape_30 ----------
def test_calculate_cape_30_computes_mean_and_std(indicator):
    data = {i: [None, None, None, None] for i in range(13)}
    data[0] = ["2025.09", "2025.10", "2025.11", "2025.12"]
    data[12] = [10, 20, 30, 40]
    df = pd.DataFrame(data)
    target_date = date(2025, 12, 15)
    promedio, desv = indicator.calculate_cape_30(df, target_date, window_size=3)
    assert promedio == pytest.approx(20.0)
    assert desv == pytest.approx(pd.Series([20, 30, 40]).std())