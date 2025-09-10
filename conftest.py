# conftest.py

import pytest
from db.db_connection import Database

@pytest.fixture(autouse=True)
def reset_db_singleton():
    """
    Antes de cada test, reinicia la instancia de Database para
    evitar contaminaciones entre tests de diferentes módulos.
    """
    Database._reset_instance()
    yield