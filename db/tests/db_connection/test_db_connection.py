from unittest import mock
import pytest
from unittest.mock import MagicMock, patch
from db.db_connection import Database

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
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{'id': 1}]
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    db = Database()
    resultado = db.execute_query("SELECT * FROM test")
    assert resultado == [{'id': 1}]

@patch('psycopg2.connect')
def test_execute_non_query(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    db = Database()
    resultado = db.execute_non_query("INSERT INTO test (id) VALUES (1)")
    assert resultado is None


@patch('psycopg2.connect')
def test_connect_establece_connection(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db = Database()
    db.connect()

    assert db._connection == mock_conn
    mock_connect.assert_called_once()

@patch('psycopg2.connect')
def test_connect_reuses_existing_connection(mock_connect):
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_connect.return_value = mock_conn

    db = Database()
    db._connection = mock_conn  # Simula conexión ya establecida
    db.connect()

    mock_connect.assert_not_called()

@patch('psycopg2.connect')
def test_get_connection_reconnects_if_closed(mock_connect):
    closed_conn = MagicMock()
    closed_conn.closed = True
    new_conn = MagicMock()
    mock_connect.return_value = new_conn

    db = Database()
    db._connection = closed_conn
    conn = db.get_connection()

    assert conn == new_conn
    mock_connect.assert_called_once()

@patch('psycopg2.connect', side_effect=Exception("Connection failed"))
def test_connect_raises_exception_on_failure(mock_connect):
    db = Database()
    with pytest.raises(Exception, match="Error al conectar a la base de datos: Connection failed"):
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