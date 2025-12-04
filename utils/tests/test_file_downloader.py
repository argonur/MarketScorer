import pytest
import io
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from utils import file_downloader

# ---------- _extract_filename ----------
def test_extract_filename_ok():
    header = 'attachment; filename="ie_data.xls"'
    assert file_downloader._extract_filename(header) == "ie_data.xls"

def test_extract_filename_none():
    assert file_downloader._extract_filename("") is None

# ---------- _get_download_links ----------
@patch("utils.file_downloader.requests.get")
def test_get_download_links_ok(mock_get):
    html = """
    <a data-aid="DOWNLOAD_DOCUMENT_LINK_RENDERED" href="file1.xls">Download</a>
    <span>ie_data</span>
    <a data-aid="DOWNLOAD_DOCUMENT_LINK_RENDERED" href="file2.xls">Download</a>
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = html.encode()
    links = file_downloader._get_download_links("http://base/")
    assert isinstance(links, list)
    assert links[0][0].startswith("http://base/file1.xls")
    assert "ie_data" in links[0][1].lower()

@patch("utils.file_downloader.requests.get")
def test_get_download_links_error_status(mock_get):
    mock_get.return_value.status_code = 500
    mock_get.return_value.content = b""
    links = file_downloader._get_download_links("http://base/")
    assert links == []

# ---------- _is_valid_ie_data ----------
def test_is_valid_ie_data_ok(tmp_path):
    # 13 columnas numéricas
    df = pd.DataFrame({str(i): range(10) for i in range(13)})
    file_path = tmp_path / "test.xlsx"
    # No forzar engine; que pandas use el disponible
    df.to_excel(file_path, sheet_name="Data", index=False)
    assert file_downloader._is_valid_ie_data(str(file_path), "ie_data")


def test_is_valid_ie_data_fail(tmp_path):
    df = pd.DataFrame({"A": range(5)})
    file_path = tmp_path / "bad.xlsx"
    df.to_excel(file_path, sheet_name="Other", index=False, engine="openpyxl")
    assert not file_downloader._is_valid_ie_data(str(file_path), "wrong")

# ---------- download_latest_file ----------
@patch("utils.file_downloader._get_download_links")
@patch("utils.file_downloader.requests.get")
def test_download_latest_file_ok(mock_req, mock_links, tmp_path):
    mock_links.return_value = [("http://fake/file.xlsx", "ie_data")]

    # Excel válido en memoria
    df = pd.DataFrame({str(i): range(10) for i in range(13)})
    buf = io.BytesIO()
    df.to_excel(buf, sheet_name="Data", index=False)
    buf.seek(0)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Disposition": 'attachment; filename="ie_data.xlsx"'}
    mock_resp.iter_content = lambda chunk_size: [buf.getvalue()]
    mock_req.return_value = mock_resp

    result = file_downloader.download_latest_file("http://base/", "data.xlsx", str(tmp_path))
    assert result is not None
    assert Path(result).exists()


@patch("utils.file_downloader._get_download_links", return_value=[])
def test_download_latest_file_no_links(mock_links, tmp_path):
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert result is None

@patch("utils.file_downloader._get_download_links", return_value=[("http://fake/file.xls", "other")])
@patch("utils.file_downloader.requests.get")
def test_download_latest_file_invalid_content(mock_req, mock_links, tmp_path):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Disposition": 'attachment; filename="wrong.xls"'}
    mock_resp.iter_content = lambda chunk_size: [b"not an excel"]
    mock_req.return_value = mock_resp
    result = file_downloader.download_latest_file("http://base/", "data.xls", str(tmp_path))
    assert result is None