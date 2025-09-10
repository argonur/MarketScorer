from unittest import mock
import pytest
from unittest.mock import MagicMock, patch
from db.db_connection import Database

# Fixture para reiniciar para reinicar la instancia de la base de datos
@pytest.fixture(autouse=True)
def reset_db_instance():
    Database._reset_instance()

@patch('psycopg2.connect')
def test_get_connection_returns_existing(mock_connect):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_connect.return_value = mock_conn

    db = Database()
    db._connection = mock_conn
    conn = db.get_connection()

    assert conn == mock_conn
    mock_connect.assert_not_called()

@patch('psycopg2.connect')
def test_execute_query(mock_connect):
    # 1) Prepara el mock de la conexión y del cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{'id': 1}]
    
    mock_conn = MagicMock()
    # Cuando se use 'with mock_conn.cursor() as cursor', cursor será mock_cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_connect.return_value = mock_conn

    # 2) Instancia DB y ejecuta query
    db = Database()
    resultado = db.execute_query("SELECT * FROM test")

    # 3) Assert: devolvió el dict esperado
    assert resultado == [{'id': 1}]

    # 4) Asegura que connect() se llamó solo una vez
    mock_connect.assert_called_once()
    # 5) Y que cursor.execute() recibió la consulta
    mock_cursor.execute.assert_called_with("SELECT * FROM test", ())

@patch('psycopg2.connect')
def test_execute_non_query(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0     # <— IMPORTANTE: define rowcount
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    db = Database()
    resultado = db.execute_non_query("INSERT INTO test (id) VALUES (1)")

    assert resultado == 0        # compara el valor, no 'is 0'
    mock_cursor.execute.assert_called_with("INSERT INTO test (id) VALUES (1)", ())

@patch('psycopg2.connect')
def test_connect_establece_connection(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db = Database()
    db.connect()

    assert db._connection is mock_conn
    mock_connect.assert_called_once()

@patch('psycopg2.connect')
def test_connect_reuses_existing_connection(mock_connect):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_connect.return_value = mock_conn

    db = Database()
    db._connection = mock_conn     # simula conexión ya establecida
    db.connect()

    # No debe volver a llamar a psycopg2.connect
    mock_connect.assert_not_called()

@patch('psycopg2.connect')
def test_get_connection_reconnects_if_closed(mock_connect):
    closed_conn = MagicMock()
    closed_conn.closed = True
    new_conn = MagicMock()
    mock_connect.return_value = new_conn

    db = Database()
    db._connection = closed_conn   # forzamos estado cerrado
    conn = db.get_connection()

    assert conn is new_conn
    mock_connect.assert_called_once()

@patch('psycopg2.connect', side_effect=Exception("Connection failed"))
def test_connect_raises_exception_on_failure(monkeypatch):
    # psycopg2.connect lanza error
    monkeypatch.setattr('psycopg2.connect', lambda *args, **kw: (_ for _ in ()).throw(Exception("Connection failed")))
    db = Database()
    with pytest.raises(Exception, match="Error al conectar a la base de datos"):
        db.connect()

def test_reset_instance_clears_singleton():
    db1 = Database()
    Database._reset_instance()
    db2 = Database()

    assert db1 is not db2

def test_reset_instance_drops_connection():
    db1 = Database()
    db1._connection = MagicMock()

    Database._reset_instance()
    db2 = Database()

    assert db2._connection is None

def test_close_closes_connection():
    mock_conn = MagicMock()
    mock_conn.closed = False

    db = Database()
    db._connection = mock_conn
    db.close()

    mock_conn.close.assert_called_once()

def test_close_skips_if_already_closed():
    mock_conn = MagicMock()
    mock_conn.closed = True

    db = Database()
    db._connection = mock_conn
    db.close()

    mock_conn.close.assert_not_called()