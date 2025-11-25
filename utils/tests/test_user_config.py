from unittest import mock
import pytest
from unittest.mock import patch, MagicMock
import db_user_config
import os
import utils.db_user_config as db_user_config

# Creamos un nuevo fixture para simular la consulta a la DB
@pytest.fixture
def mock_conn_cursor():
    """Fixture que mockea la conexión y cursor de psycopg2."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor

@patch("db_user_config.psycopg2.connect")
def test_get_user_config_encontrado(mock_connect, mock_conn_cursor, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Simulamos el fetchone que devuelve datos de la DB
    mock_cursor.fetchone.return_value = {"bot_token": "TOKEN123", "chat_id": "12345"}
    resultado = db_user_config.get_user_config("test@example.com")
    
    assert resultado == {"BOT_TOKEN": "TOKEN123", "CHAT_ID": "12345"}
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

@patch("db_user_config.psycopg2.connect")
def test_get_user_config_no_encontrado(mock_connect, mock_conn_cursor, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Simulamos el fetchone que devuelva None
    mock_cursor.fetchone.return_value = None

    resultado = db_user_config.get_user_config("test@example.com")

    assert resultado is None
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

# Agregar tests que valide el ValueError de get_user_config

@patch("db_user_config.psycopg2.connect")
def test_set_user_config_user_existente(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Simulamos que el usuario ya existe
    mock_cursor.fetchone.return_value = (1,)
    db_user_config.set_user_config("existente@example.com", "9999")

    captured = capsys.readouterr()
    assert "ya existe" in captured.out
    assert not any("INSERT INTO user_configs" in c[0][0] for c in mock_cursor.execute.call_args_list)
    mock_conn.commit.assert_not_called()

@patch("db_user_config.psycopg2.connect")
def test_set_user_config_new_user(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Simular que el usuario no existe
    mock_cursor.fetchone.return_value = None

    # Ejecutar la función bajo prueba
    db_user_config.set_user_config("new@example.com", "5555")

    # Capturar salida
    captured = capsys.readouterr()
    assert "Usuario agregado" in captured.out

    # Verificar que hubo una llamada INSERT con los parámetros correctos
    insert_call = None
    for call_args in mock_cursor.execute.call_args_list:
        sql, params = call_args[0]  # argumentos posicionales
        if "INSERT INTO user_configs" in sql:
            insert_call = (sql, params)
            break

    assert insert_call is not None, "No se encontró la llamada INSERT"
    sql, params = insert_call
    assert params == ("new@example.com", db_user_config.BOT_TOKEN, "5555")
    mock_conn.commit.assert_called_once()

@patch("db_user_config.psycopg2.connect")
def test_update_user_config_current_no_existe(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Simular que el identificador actual no existe
    mock_cursor.fetchone.side_effect = [None]
    db_user_config.update_user_config("missing@example.com", "new@example.com", "4444")
    
    captured = capsys.readouterr()
    assert "no existe" in captured.out

@patch("db_user_config.psycopg2.connect")
def test_update_user_config_new_identifier_already_exist(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Primer SELECT -> existe el usuario actual
    # Segundo SELECT -> nuevo identificador ya en uso

    mock_cursor.fetchone.side_effect = [(1,), (1,)]
    db_user_config.update_user_config("old@example.com", "exist@example.com", "2222")

    captured = capsys.readouterr()
    assert "ya está en uso" in captured.out

@patch("db_user_config.psycopg2.connect")
def test_update_user_config_exitoso(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn

    # Primer SELECT -> usuario actual existe
    # Segundo SELECT -> nuevo identificador no existe

    mock_cursor.fetchone.side_effect = [(1,), None]

    db_user_config.update_user_config("old@example.com", "new@example.com", "1111")
    captured = capsys.readouterr()
    assert "Usuario actualizado" in captured.out

    update_call = None
    for call_args in mock_cursor.execute.call_args_list:
        sql, params = call_args[0] # argumentos posicionales
        if "UPDATE user_configs" in sql:
            update_call = (sql, params)
            break
    assert update_call is not None, "No se encontro la llamada UPDATE"
    sql, params = update_call
    assert params == ("new@example.com", "1111", "old@example.com")
    mock_conn.commit.assert_called_once()

@patch("db_user_config.psycopg2.connect")
def test_update_user_config_sin_cambio_de_identifier(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn
    # existe el actual
    mock_cursor.fetchone.return_value = (1,)

    db_user_config.update_user_config("same@example.com", "same@example.com", "7777")
    captured = capsys.readouterr()
    assert "Usuario actualizado" in captured.out

    # Asegura que NO se hizo el segundo SELECT
    executes = [args[0] for args, _ in mock_cursor.execute.call_args_list]
    assert sum("SELECT 1 FROM user_configs WHERE identifier = %s" in sql for sql in executes) == 1

    # Verifica el UPDATE y parámetros
    update_call = next((c for c in mock_cursor.execute.call_args_list if "UPDATE user_configs" in c[0][0]), None)
    assert update_call is not None
    _, params = update_call[0]
    assert params == ("same@example.com", "7777", "same@example.com")

##### Pruebas para los try-except #####
@patch("db_user_config.psycopg2.connect", side_effect=Exception("boom"))
def test_get_user_config_exception_print_y_cierre(mock_connect, mock_conn_cursor, capsys):
    # DB_URL valido
    with patch.object(db_user_config, "DB_URL", "postgres://test"):
        res = db_user_config.get_user_config("test@example.com")
        captured = capsys.readouterr()
        assert "No se pudo obtener" in captured.out
        assert res is None

@patch("db_user_config.psycopg2.connect")
def test_set_user_config_except_en_insert(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn
    mock_cursor.fetchone.return_value = None
    # Falla el INSERT INTO

    def fail_on_insert(sql, params):
        if "INSERT INTO user_configs" in sql:
            raise Exception("insert failed")
    mock_cursor.execute.side_effect = fail_on_insert

    db_user_config.set_user_config("test@example.com", "1111")
    captured = capsys.readouterr()
    assert "Error al insertar" in captured.out
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

@patch("db_user_config.psycopg2.connect")
def test_update_user_config_except_en_update(mock_connect, mock_conn_cursor, capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn, mock_cursor = mock_conn_cursor
    mock_connect.return_value = mock_conn
    mock_cursor.fetchone.side_effect = [(1,), None]  # existe actual, nuevo libre
    def fail_on_update(sql, params):
        if "UPDATE user_configs" in sql:
            raise Exception("update failed")
    mock_cursor.execute.side_effect = fail_on_update

    db_user_config.update_user_config("old@example.com", "new@example.com", "1111")
    captured = capsys.readouterr()
    assert "Error al actualizar usuario" in captured.out
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


##### Pruebas para la variable de entorno de DB_URL #####
def test_get_user_config_value_error_db_url(monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", None)
    with pytest.raises(ValueError):
        db_user_config.get_user_config("x@example.com")

def test_set_user_config_value_error_db_url(monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "")
    with pytest.raises(ValueError):
        db_user_config.set_user_config("x@example.com", "111")

def test_update_user_config_value_error_db_url(monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", 0)
    with pytest.raises(ValueError):
        db_user_config.update_user_config("new@example.com", "old@example.com","2222")

def test_set_user_cursor_falla_cierra_solo_conn(capsys, monkeypatch):
    # Creamos un mock de conexión con close espiable
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("falló el cursor")

    with patch("psycopg2.connect", return_value=mock_conn):
        # Ejecutamos la función que abre la conexion y luego falla
        db_user_config.set_user_config("test@example", "1111")

        # Capturamos stdout/stderr para verificar el mensaje
        out, err = capsys.readouterr()
        assert "falló el cursor" in out or err

        # Verificamos que se haya cerrado el cursor inexistente
        mock_conn.close.assert_called_once()

def test_update_cursor_falla_cierra_solo_conn(capsys, monkeypatch):
    # Creamos un mock de conexión con close espiable
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("falló el cursor")

    with patch("psycopg2.connect", return_value=mock_conn):
        # Ejecutamos la función que abre la conexion y luego falla
        db_user_config.update_user_config("test@example", "new@example", "1111")

        # Capturamos stdout/stderr para verificar el mensaje
        out, err = capsys.readouterr()
        assert "falló el cursor" in out or err

        # Verificamos que se haya cerrado el cursor inexistente
        mock_conn.close.assert_called_once()

def test_set_user_connect_falla_imprime_error_no_intenta_cerrar(capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mensaje = "falló conexión"

    # Simulamos que psycopg2.connect lanza excepcion al intentar abrir una conexion
    with patch("psycopg2.connect", side_effect=Exception(mensaje)) as mock_connect:
        # La funcion deberia propagar la excepcion
        db_user_config.set_user_config("test@example.com", "1111")

    # Verificamos que el mensaje de error se imprime
    out, err = capsys.readouterr()
    assert (mensaje in out) or (mensaje in err)

    # Nos aseguramos que el intento de conexión ocurrio exactamente una vez
    mock_connect.assert_called_once()

def test_update_user_connect_falla_imprime_error_no_intenta_cerrar(capsys, monkeypatch):
    monkeypatch.setattr(db_user_config, "DB_URL", "postgresql://fake_user:fake_pass@localhost:5432/fake_db")
    mensaje = "falló conexión"

    # Simulamos que psycopg2.connect lanza excepcion al intentar abrir una conexion
    with patch("psycopg2.connect", side_effect=Exception(mensaje)) as mock_connect:
        # La funcion deberia propagar la excepcion
        db_user_config.update_user_config("test@example.com", "new@example","1111")

    # Verificamos que el mensaje de error se imprime
    out, err = capsys.readouterr()
    assert (mensaje in out) or (mensaje in err)

    # Nos aseguramos que el intento de conexión ocurrio exactamente una vez
    mock_connect.assert_called_once()