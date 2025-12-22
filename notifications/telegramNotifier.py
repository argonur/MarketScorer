import os
import requests
import logging
from datetime import timezone, timedelta
import data.market_dates as md
from utils.db_user_config import get_user_config
from core.scoreCalculator import ScoreCalculator, valid_weight
from data.market_dates import get_last_trading_close
from indicators.spxIndicator import SPXIndicator
from indicators.FearGreedIndicator import FearGreedIndicator
from indicators.vixIndicator import VixIndicator
from indicators.shillerPEIndicator import ShillerPEIndicator

logger = logging.getLogger(__name__)
LOCAL_TZ = timezone(timedelta(hours=-6))
SIMBOL = '^SPX'

def valoracion_feargreed(fg_valor):
    if not fg_valor:
        return None
    try:
        descripcion = (fg_valor.description or "").strip().lower()
        simbolo = {
            'extreme fear': '🔴',
            'fear': '🟡',
            'greed': '🟢',
            'extreme greed': '🟢'
        }.get(descripcion, '⚪')
        valor = round(float(fg_valor.value))
        return f"{valor} {simbolo} {descripcion or 'unknow'}"
    except Exception:
        return None

class TelegramNotifier:
    def __init__(self, post_fn=requests.post, config_fn=get_user_config, getenv_fn=os.getenv):
        self._post = post_fn
        self._get_config = config_fn
        self._getenv = getenv_fn

    def _resolve_config(self):
        bot_token = self._getenv('BOT_TOKEN')
        chat_id = self._getenv('CHAT_ID')
        user_identifier = self._getenv('USER_IDENTIFIER')

        if not bot_token or not chat_id:
            logger.warning("BOT_TOKEN o CHAT_ID no encontrados en entorno, buscando en DB...")
            user_config = self._get_config(user_identifier)
            if not user_config:
                raise ValueError(f"No se encontró configuración para {user_identifier}")
            bot_token = user_config.get("BOT_TOKEN")
            chat_id = user_config.get("CHAT_ID")
        return bot_token, chat_id

    def enviar_mensaje(self, mensaje: str) -> bool:
        bot_token, chat_id = self._resolve_config()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}
        response = self._post(url, data=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Error enviando mensaje: {response.text}")
        logger.info("Mensaje enviado correctamente a Telegram")
        return True

def generar_reporte_mercado(
    spx_cls=SPXIndicator,
    fg_cls=FearGreedIndicator,
    vix_cls=VixIndicator,
    shiller_cls=ShillerPEIndicator,
    score_cls=ScoreCalculator
) -> str:
    spx = spx_cls()
    fg = fg_cls()
    vix = vix_cls()
    shiller = shiller_cls()

    pesos = {
        "SPXIndicator": valid_weight("spx"),
        "FearGreedIndicator": valid_weight("fear_greed"),
        "VixIndicator": valid_weight("vix"),
        "ShillerPEIndicator": valid_weight("shiller")
    }
    calculator = score_cls(indicators=[spx, fg, vix, shiller], weights=pesos)
    date_to_calculate = get_last_trading_close().date()
    score_final = round(calculator.get_global_score(date_to_calculate))

    fg_val = fg.fetch_data(date_to_calculate)
    value_fg = valoracion_feargreed(fg_val) or "N/A"
    hora_local = md.market_now().astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

    return (
        f"<b>📊 Reporte Mercado</b>\n"
        f"🕟 Date: {hora_local}\n"
        f"📰 CNN Fear & Greed: <b>{value_fg}</b>\n"
        f"📈 SMA-200 S&P 500: <b>{spx.normalize(date_to_calculate):.2f}</b>\n"
        f"🏛️ Calculo SMA-200 S&P500: <b>{spx.fetch_data(date_to_calculate):.2f}</b>\n"
        f"📰 Valor normalizado de Vix: <b>{vix.normalize(date_to_calculate):.2f}</b>\n"
        f"📰 Valor normalizado de Shiller PE: <b>{shiller.get_score(date_to_calculate):.2f}</b>\n"
        f"💰 Último Cierre S&P 500: <b>{spx.get_last_close(SIMBOL, date_to_calculate):.2f}</b>\n"
        f"🧾 Score Final: <b>{score_final}%</b>\n"
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        logger.info("Iniciando generación de reporte de mercado...")
        reporte = generar_reporte_mercado()
        notifier = TelegramNotifier()
        notifier.enviar_mensaje(reporte)
        logger.info("Workflow completado correctamente.")
    except Exception as e:
        logger.exception("Error fatal en el workflow")
        raise
