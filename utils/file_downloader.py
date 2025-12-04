import os
from pathlib import Path
from urllib.parse import urljoin
import tempfile
import requests
from bs4 import BeautifulSoup
import pandas as pd

TARGET_LABEL = os.getenv("SHILLER_PE_FILE_NAME", "ie_data")  # patrón de nombre esperado

def download_latest_file(base_url: str, file_name: str, save_dir: str) -> str | None:
    try:
        candidates = _get_download_links(base_url)
        if not candidates:
            print("❌ No se encontraron enlaces de descarga.")
            return None

        os.makedirs(save_dir, exist_ok=True)
        final_path = Path(save_dir) / "latest.xls"

        # Probar cada enlace y validar contenido
        for url, near_text in candidates:
            # Log de para depuración 
            #print(f"⏳ Probando candidato: {url} (contexto: '{near_text}')")
            try:
                resp = requests.get(url, timeout=45, stream=True)
                if resp.status_code != 200:
                    print(f"⚠️ HTTP {resp.status_code} en {url}")
                    continue

                # Nombre por Content-Disposition si existe
                content_disp = resp.headers.get("Content-Disposition", "")
                filename = _extract_filename(content_disp) or ""
                name_hint = filename or near_text

                # Guardar temporalmente y validar abriendo el Excel
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xls") as tmp:
                    for chunk in resp.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            tmp.write(chunk)
                    tmp_path = tmp.name

                if _is_valid_ie_data(tmp_path, name_hint):
                    # Guardar definitivo
                    with open(final_path, "wb") as out_f, open(tmp_path, "rb") as in_f:
                        out_f.write(in_f.read())
                    print(f"✅ Archivo correcto guardado en: {final_path}")
                    return str(final_path)
                else:
                    # Log de depuración
                    #print("⚠️ Candidato descartado por validación de contenido.")
                    continue
            except Exception as e:
                print(f"⚠️ Error evaluando candidato {url}: {e}")
                continue

        print("❌ Ningún enlace produjo un Excel válido para ie_data.")
        return None

    except Exception as e:
        print(f"❌ Error general en download_latest_file: {e}")
        return None


def _get_download_links(base_url: str) -> list[tuple[str, str]]:
    """
    Retorna lista de (absolute_url, near_text) para todos los anchors de descarga.
    """
    try:
        resp = requests.get(base_url, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"Error al cargar la página: {resp.status_code}")

        soup = BeautifulSoup(resp.content, "html.parser")
        anchors = soup.find_all("a", {"data-aid": "DOWNLOAD_DOCUMENT_LINK_RENDERED"})
        results: list[tuple[str, str]] = []

        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            abs_url = urljoin(base_url, href)

            # Texto cercano para ayudar a identificar
            span_next = a.find_next("span")
            near_text = (span_next.get_text(strip=True) if span_next else "")
            if not near_text:
                near_text = a.get_text(strip=True) or ""

            results.append((abs_url, near_text))

        # Priorizar los que ya mencionan el patrón
        prioritized = sorted(results, key=lambda x: 0 if TARGET_LABEL.lower() in (x[1] or "").lower() else 1)
        return prioritized

    except Exception as e:
        print(f"❌ Error al extraer enlaces de descarga: {e}")
        return []


def _extract_filename(content_disposition: str) -> str | None:
    if not content_disposition:
        return None
    parts = [p.strip() for p in content_disposition.split(";")]
    for p in parts:
        if p.lower().startswith("filename="):
            return p.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _is_valid_ie_data(tmp_path: str, name_hint: str) -> bool:
    """
    Validación del Excel:
    - Hoja 'Data' presente.
    - Al menos 13 columnas.
    - Columnas 10 y 12 con datos numéricos y no vacíos.
    - Si el nombre sugiere 'ie_data', suma confianza pero no es obligatorio.
    """
    try:
        ext = Path(tmp_path).suffix.lower()  # '.xls' o '.xlsx'
        engine = None
        if ext == ".xls":
            engine = "xlrd"
        elif ext == ".xlsx":
            engine = "openpyxl"

        # Abrir archivo con engine elegido; si falla, intentar sin engine
        try:
            xls = pd.ExcelFile(tmp_path, engine=engine) if engine else pd.ExcelFile(tmp_path)
        except Exception:
            xls = pd.ExcelFile(tmp_path)  # fallback

        if "Data" not in xls.sheet_names:
            return False

        try:
            df = pd.read_excel(tmp_path, sheet_name="Data", engine=engine) if engine else pd.read_excel(tmp_path, sheet_name="Data")
        except Exception:
            df = pd.read_excel(tmp_path, sheet_name="Data")  # fallback

        if df.shape[1] < 13:
            return False

        col10 = pd.to_numeric(df.iloc[:, 10], errors="coerce").dropna()
        col12 = pd.to_numeric(df.iloc[:, 12], errors="coerce").dropna()
        if col10.empty or col12.empty:
            return False

        # Nombre sugerido suma, pero no bloquea si el contenido es válido
        return True

    except Exception:
        return False