import os
import requests
from dotenv import load_dotenv
from indicators.spxIndicator import SPXIndicator
from indicators.FearGreedIndicator import FearGreedIndicator
from indicators.vixIndicator import VixIndicator
from indicators.shillerPEIndicator import ShillerPEIndicator
from core.scoreCalculator import ScoreCalculator, valid_weight
from utils.db_user_config import get_user_config
#from data.market_dates import market_now
import data.market_dates as md
from datetime import datetime, timedelta, timezone

load_dotenv()

# Zona horaria local (GMT-6)
LOCAL_TZ = timezone(timedelta(hours=-6))

# Este modulo unicamente envia notificaciones con respecto al calculo del modulo ScorerCalculator

def valoracion_feargreed(fg_valor):
    """
    Devuelve None si no hay datos válidos.
    fg_valor debe tener .value (numérico) y .description (str).
    """
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

    def enviar_mensaje(self, mensaje: str) -> None:
        """Enviar mensaje simple por mensajería a Telegram."""
        bot_token = self._getenv('BOT_TOKEN')
        chat_id = self._getenv('CHAT_ID')
        user_identifier = self._getenv('USER_IDENTIFIER')

        # Verificamos la conexion a la base de datos o variables de entorno
        if not bot_token or not chat_id:
            print("BOT_TOKEN O CHAT_ID no encontrados en el sistema. Buscando en la base de datos.....")
            user_config = self._get_config(user_identifier)
            if user_config:
                bot_token = user_config.get("BOT_TOKEN")
                chat_id = user_config.get("CHAT_ID")
            else:
                raise ValueError(
                    f"No se encontro una configuración para {user_identifier}."
                    " Por favor crea un nuevo usuario para poder recibir las notificaciones."
                    )
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML"  # Usamos HTML para formatear el mensaje
        }
        response = self._post(url, data=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Error enviando el mensaje: {response.text}")
        return True

    @staticmethod
    def enviar_reporte_mercado(post_fn=requests.post, config_fn=get_user_config,
        getenv_fn=os.getenv, spx_cls=SPXIndicator,
        fg_cls=FearGreedIndicator, vix_cls=VixIndicator, shiller_cls = ShillerPEIndicator, score_cls=ScoreCalculator) -> str:

        """
        Calcula indicadores, arma el mensaje y lo envía.
        Devuelve el mensaje formateado para facilitar tests.
        """
        # 1️⃣ Instancias inyectables para tests

        spx_sma = spx_cls()
        fear_greed = fg_cls()
        vix = vix_cls()
        shiller = shiller_cls()


        # 2️⃣ Obtener pesos
        spx_weight = valid_weight("spx")
        fear_greed_weight = valid_weight("fear_greed")
        vix_weight = valid_weight("vix")
        shiller_weight = valid_weight("shiller")

        pesos = {
            "SPXIndicator": spx_weight,
            "FearGreedIndicator": fear_greed_weight,
            "VixIndicator": vix_weight,
            "ShillerPEIndicator": shiller_weight
        }

        # 3️⃣ Calcular score final
        calculator = score_cls(
            indicators=[spx_sma, fear_greed, vix, shiller],
            weights=pesos
        )

        score_final = round(calculator.calculate_score())

        # 4️⃣ Obtener valores de indicadores
        fg_val = fear_greed.fetch_data() # Recibe el valor real de la API
        value_fg = valoracion_feargreed(fg_val) or "N/A"
        spx_sma200_valor = spx_sma.normalize()
        calculo_sma200 = spx_sma.fetch_data()
        spx_ultimo_cierre = spx_sma.get_last_close(SIMBOL="^SPX")
        vix_normalizado = vix.normalize()
        shiller_normalizado = shiller.get_score()

        hora_local = md.market_now().astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

        # 5️⃣ Formatear mensaje
        mensaje = (
            f"<b>📊 Reporte Mercado</b>\n"
            f"🕟 Date: {hora_local}\n"
            f"📰 CNN Fear & Greed: <b>{value_fg}</b>\n"
            f"📈 SMA-200 S&P 500: <b>{spx_sma200_valor:.2f}</b>\n"
            f"🏛️ Calculo SMA-200 S&P500: <b>{calculo_sma200:.2f}</b>\n"
            f"📰 Valor normalizado de Vix: <b>{vix_normalizado:.2f}</b>\n"
            f"📰 Valor normalizado de Sheller PE: <b>{shiller_normalizado:.2f}</b>\n"
            f"💰 Último Cierre S&P 500: <b>{spx_ultimo_cierre:.2f}</b>\n"
            f"🧾 Score Final: <b>{score_final}%</b>\n"
        )

        notifier = TelegramNotifier(post_fn=post_fn, config_fn=config_fn, getenv_fn=getenv_fn)
        notifier.enviar_mensaje(mensaje)
        print(f"✅ Notificacion enviada a Telegram")
        return mensaje

if __name__ == "__main__":
        TelegramNotifier.enviar_reporte_mercado()