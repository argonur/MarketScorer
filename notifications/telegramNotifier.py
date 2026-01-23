# notifications/telegramNotifier.py
import os
import requests
import logging
import json
from datetime import timezone, timedelta, datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
LOCAL_TZ = timezone(timedelta(hours=-6))

def valoracion_feargreed(fg_valor):
    """Función auxiliar para formatear la valoración de Fear & Greed
    a partir del diccionario de datos obtenido del JSON."""
    if not fg_valor or not isinstance(fg_valor, dict):
        return None
    try:
        raw_value = fg_valor.get("raw_value")   # Segun la estructura de datos market_report.json
        descripcion = fg_valor.get("raw_description", "").strip().lower()

        simbolo = {
            'extreme fear': '🔴',
            'fear': '🟡',
            'greed': '🟢',
            'extreme greed': '🟢'
        }.get(descripcion, '⚪')

        # Se busca el valor crudo en el JSON
        valor = int(raw_value) if raw_value is not None else -1
        return f"{valor} {simbolo} {descripcion or 'unknown'}"
    except (ValueError, TypeError):
        logger.error(f"Error al parsear datos del Fear Greed desde el JSON", exc_info=True)
        return None

class TelegramNotifier:
    def __init__(self, report_file_path="data/market_report.json", post_fn=requests.post, config_fn=None, getenv_fn=os.getenv):
        """
        Args:
            report_file_path (str): Ruta al archivo JSON con los datos del reporte.
            post_fn (callable): Función para hacer POST (para inyección de dependencias).
            config_fn (callable): Función para obtener configuración (puede ser None si solo se usa entorno).
            getenv_fn (callable): Función para obtener variables de entorno.
        """
        self.report_file_path = report_file_path
        self._post = post_fn
        # Si no se pasa config_fn, se usa la función predeterminada
        self._get_config = config_fn if config_fn else lambda x: {}
        self._getenv = getenv_fn

    def _resolve_config(self):
        bot_token = self._getenv('BOT_TOKEN')
        chat_id = self._getenv('CHAT_ID')
        user_identifier = self._getenv('USER_IDENTIFIER')

        if not bot_token or not chat_id:
            logger.warning("BOT_TOKEN o CHAT_ID no encontrados en entorno, buscando en DB...")
            #user_config = self._get_config(user_identifier)
            #if not user_config:
            raise ValueError(f"No se encontró configuración para {user_identifier}")
            #bot_token = user_config.get("BOT_TOKEN")
            #chat_id = user_config.get("CHAT_ID")
        return bot_token, chat_id

    def load_market_report(self):
        """ Carga y devuelve los datos del JSON """
        if not os.path.exists(self.report_file_path):
            raise FileNotFoundError(f"No se encontro el archivo: {self.report_file_path}")

        with open(self.report_file_path, 'r', encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not data: # Verifica si el diccionario resultante está vacío
                    raise ValueError(f"El archivo {self.report_file_path} esta vacio")
                return data
            except json.JSONDecodeError as e:
                raise ValueError(f"Error al leer el archivo JSON: -> {e}")

    def generar_reporte_desde_cache(self) -> str:
        try:
            data = self.load_market_report()

            calc_date_str = data.get("SPXIndicator", {}).get("calc_date", "Fecha desconocida")
            # Se asume que el formato de la fecha (str) es "YYYY-MM-DD"
            try:
                calc_date_obj = datetime.strptime(calc_date_str, "%Y-%m-%d").date()
            except ValueError:
                calc_date_obj = None

            # Intentamos tomar la fecha timestamp del archivo del SPX como base
            spx_timestamp_str = data.get("SPXIndicator", {}).get("timestamp", "")
            fecha_calculo = data.get("SPXIndicator", {}).get("calc_date", "")
            try:
                # Formato de timestamp ISO 8601
                # Añadir Z si no está presente para que fromisoformat lo reconozca como UTC
                timestamp_iso = spx_timestamp_str
                if not timestamp_iso.endswith('Z'):
                     timestamp_iso += 'Z' # Asume UTC si no tiene offset
                timestamp_dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
                hora_local = timestamp_dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                # Si no se puede parsear el timestamp, se usa una fecha del calculo.
                hora_local = calc_date_str if calc_date_obj else "Fecha/Hora desconocida"

            # - Fear and Greed
            fg_data = data.get("FearGreedIndicator", {})
            value_fg = valoracion_feargreed(fg_data) or "N/A"

            # - SPX
            spx_data = data.get("SPXIndicator", {})
            sma_normalized = spx_data.get("normalized_value", float('nan'))
            sma_value = spx_data.get("sma_value", float('nan'))
            last_close_spx = spx_data.get("last_close", float('nan'))

            # - Vix
            vix_data = data.get("VixIndicator", {})
            normalized_vix = vix_data.get("normalized_value", float('nan'))

            # - ShillerPE
            shiller_data = data.get("ShillerPEIndicator", {})
            normalized_shiller = shiller_data.get("normalized_score", float('nan'))

            # - ScoreCalculator
            score_data = data.get("score_calculator", {})
            score_final = score_data.get("value", float('nan'))

            # - Formato del mensaje
            def safe_format(val, fmt="{:.2f}"):
                is_nan = isinstance(val, float) and (val != val)
                return fmt.format(val) if val is not None and not is_nan else "N/A"

            return (
                f"<b>📊 Reporte Mercado: </b>{fecha_calculo}\n"
                f"🕟 Date: {hora_local}\n" # Fecha usada para el calculo de ScoreCalculator
                f"📰 CNN Fear & Greed: <b>{value_fg}</b>\n"
                f"📈 SMA-200 S&P 500: <b>{safe_format(sma_normalized)}</b>\n"
                f"📝 Calculo SMA-200 S&P500: <b>{safe_format(sma_value)}</b>\n"
                f"📋 Valor normalizado de Vix: <b>{safe_format(normalized_vix)}</b>\n"
                f"📋 Valor normalizado de Shiller PE: <b>{safe_format(normalized_shiller)}</b>\n"
                f"💰 Último Cierre S&P 500: <b>{safe_format(last_close_spx)}</b>\n"
                f"✅ Score Final: <b>{safe_format(score_final)}%</b>\n"
            )

        except FileNotFoundError as e:
            logger.error(f"[generar_reporte_desde_cache] Archivo no encontrado: {e}")
            raise
        except ValueError as e:
            logger.error(f"[generar_reporte_desde_cache] Error de datos: {e}")
            raise
        except Exception as e:
            logger.error(f"[generar_reporte_desde_cache] Ocurrio un error inesperado: {e}", exc_info=True)
            raise

    def enviar_mensaje(self, mensaje: str) -> bool:
        bot_token, chat_id = self._resolve_config()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}

        response = self._post(url, data=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Error enviando mensaje: {response.text}")

        logger.info("Mensaje enviado correctamente a Telegram")
        return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    notifier = TelegramNotifier(report_file_path="data/market_report.json")

    try:
        logger.info("Iniciando generación de reporte de mercado...")
        reporte = notifier.generar_reporte_desde_cache()
        notifier.enviar_mensaje(reporte)
        logger.info("Workflow completado correctamente.")
    except Exception as e:
        logger.exception("Error fatal en el workflow de TelegramNotifier.")
        raise
