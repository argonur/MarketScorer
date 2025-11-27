import pytest
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from utils import file_downloader

# ---------- _get_download_url ----------
@patch("utils.file_downloader.requests.get")
def test_get_download_url_ok(mock_get):
    html = '<a data-aid="DOWNLOAD_DOCUMENT_LINK_RENDERED" href="file.xls">Download </a>'
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = html.encode()
    url = file_downloader._get_download_url("http://base/")
    assert url == "http://base/file.xls"

@patch("utils.file_downloader.requests.get")
def test_get_download_url_error_status(mock_get, capsys):
    mock_get.return_value.status_code = 500
    mock_get.return_value.content = b""
    url = file_downloader._get_download_url("http://base/")
    assert url is None
    captured = capsys.readouterr()
    assert "Error al cargar la" in captured.out

@patch("utils.file_downloader.requests.get")
def test_get_download_url_no_button(mock_get, capsys):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"<html></html>"
    url = file_downloader._get_download_url("http://base/")
    assert url is None
    captured = capsys.readouterr()
    assert "No se encontró el botón" in captured.out

# ---------- download_latest_file ----------
@patch("utils.file_downloader.get_last_trading_date")
@patch("utils.file_downloader._get_download_url", return_value = "http://fake/file.xls")
@patch("utils.file_downloader.requests.get")
def test_download_latest_file_new(mock_req, mock_url, mock_date, tmp_path):
    mock_date.return_value = file_downloader.datetime(2024, 1, 1).date()
    mock_req.return_value.status_code = 200
    mock_req.return_value.content = b"contenido"
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert Path(result).exists()
    assert Path(result).read_bytes() == b"contenido"

@patch("utils.file_downloader.get_last_trading_date")
@patch("utils.file_downloader._get_download_url", return_value = None)
def test_download_latest_file_no_url(mock_url, mock_date, tmp_path, capsys):
    mock_date.return_value = file_downloader.datetime(2024, 1, 1).date()
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert result is None
    captured = capsys.readouterr()
    assert "No se pudo obtener" in captured.out

# ---------- Cubrir las excepciones ----------
@patch("utils.file_downloader.get_last_trading_date")
@patch("utils.file_downloader._get_download_url", return_value=None)
def test_download_latest_file_no_url(mock_url, mock_date, tmp_path, capsys):
    mock_date.return_value = file_downloader.datetime(2024,1,1).date()
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert result is None
    captured = capsys.readouterr()
    assert "❌ No se pudo obtener la URL" in captured.out

@patch("utils.file_downloader.get_last_trading_date")
@patch("utils.file_downloader._get_download_url", return_value="http://fake/file.xls")
@patch("utils.file_downloader.requests.get")
def test_download_latest_file_error_descarga(mock_req, mock_url, mock_date, tmp_path, capsys):
    mock_date.return_value = file_downloader.datetime(2024,1,1).date()
    mock_req.return_value.status_code = 404
    mock_req.return_value.content = b""
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert result is None
    captured = capsys.readouterr()
    assert "❌ Error al descargar el archivo" in captured.out

@patch("utils.file_downloader.get_last_trading_date")
@patch("utils.file_downloader._get_download_url", side_effect=Exception("boom"))
def test_download_latest_file_excepcion_general(mock_url, mock_date, tmp_path, capsys):
    mock_date.return_value = file_downloader.datetime(2024,1,1).date()
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert result is None
    captured = capsys.readouterr()
    assert "Error al descargar el archivo" in captured.out

@patch("utils.file_downloader.requests.get", side_effect=Exception("fallo requests"))
def test_get_download_url_excepcion(mock_req, capsys):
    url = file_downloader._get_download_url("http://base/")
    assert url is None
    captured = capsys.readouterr()
    assert "❌ Error al obtener la URL de descarga" in captured.out