import json
import logging
from psycopg2 import DatabaseError
from db.db_connection import Database
from data.market_dates import market_now
from config.config_loader import get_config
from indicators.FearGreedIndicator import FearGreedIndicator
from indicators.spxIndicator import SPXIndicator, SIMBOL
from indicators.vixIndicator import VixIndicator
from core.scoreCalculator import ScoreCalculator

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="❌ %(asctime)s %(message)s"
)

class ScorerBackup:
    def __init__(self, db=None):
        self.db = db or Database()
        self.calc_date = market_now().date()
        self.config    = get_config()
        # instancias de indicadores
        self.fg = FearGreedIndicator()
        self.sp = SPXIndicator()
        self.vx = VixIndicator()

    @staticmethod
    def to_native(val):
        """Convierte np.generic a nativo Python."""
        if hasattr(val, "item"):
            return val.item()
        return val

    def backup_config(self):
        try:
            sql = """
            INSERT INTO config_backup
                (calc_date, config_json, weight_fear_greed, weight_spx, weight_vix,
                backtest_start, backtest_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (calc_date) DO UPDATE
                SET config_json       = EXCLUDED.config_json,
                    weight_fear_greed = EXCLUDED.weight_fear_greed,
                    weight_spx        = EXCLUDED.weight_spx,
                    weight_vix        = EXCLUDED.weight_vix,
                    backtest_start    = EXCLUDED.backtest_start,
                    backtest_end      = EXCLUDED.backtest_end
            RETURNING id, (xmax = 0)
            """
            w = self.config["weights"]
            params = [
                self.calc_date,
                json.dumps(self.config),
                w.get("fear_greed"),
                w.get("spx"),
                w.get("vix"),
                self.config["backtesting"]["start_date"],
                self.config["backtesting"]["end_date"],
            ]
            result = self.db.execute_query(sql, params)
            return result[0]["id"]
        except DatabaseError as db_error:
            self.db.get_connection().rollback()
            raise RuntimeError("Error al respaldar la configuración") from db_error

    def backup_fear_greed(self, cfg_id):
        try: 
            raw = self.fg.fetch_data()
            params = [
                self.calc_date,
                round(self.to_native(raw.value)),
                raw.description,
                round(self.to_native(self.fg.normalize()), 2)
            ]
            sql = """
            INSERT INTO fear_greed_backup
                (calc_date, raw_value, description, normalized_value)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (calc_date) DO NOTHING
            """
            insertado = self.db.execute_non_query(sql, params)
            if insertado == 0:
                logger.warning("[backup_fear_greed]: No se insertaron los registros para %s: ya existen", self.calc_date)
            # opcional: devolver ID si lo necesitas
        except (ValueError, DatabaseError) as err:
            self.db.get_connection().rollback()
            raise RuntimeError("Error al respaldar FearGreedIndicator") from err

    def backup_spx(self, cfg_id):
        try: 
            raw = self.sp.fetch_data()
            params = [
                self.calc_date,
                self.sp.sma_period,
                round(self.to_native(self.sp.get_last_close(SIMBOL)), 2),
                round(self.to_native(raw), 2),
                round(self.to_native(self.sp.normalize()), 2)
            ]
            sql = """
            INSERT INTO spx_backup
                (calc_date, sma_period, last_close, spx_sma, normalized_value)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (calc_date) DO NOTHING
            """
            insertado = self.db.execute_non_query(sql, params)
            if insertado == 0:
                logger.warning("[backup_spx]: No se insertaron los registros para %s: ya existen", self.calc_date)
        except (ValueError, DatabaseError) as err:
            self.db.get_connection().rollback()
            raise RuntimeError("Error al respaldar SPXIndicator") from err

    def backup_vix(self, cfg_id):
        try:
            raw = self.vx.fetch_data()
            params = [
                self.calc_date,
                round(self.to_native(raw), 2),
                round(self.to_native(self.vx.normalize()), 2)
            ]
            sql = """
            INSERT INTO vix_backup
                (calc_date, raw_value, normalized_value)
            VALUES (%s, %s, %s)
            ON CONFLICT (calc_date) DO NOTHING
            """
            insertado = self.db.execute_non_query(sql, params)
            if insertado == 0:
                logger.warning("[backup_vix]: No se insertaron los registros para  %s: ya existen", self.calc_date)
        except (ValueError, DatabaseError) as err:
            self.db.get_connection().rollback()
            raise RuntimeError("Error al respaldar VixIndicator") from err

    def backup_score(self, cfg_id):
        try:
            score = ScoreCalculator.get_global_score()
            sql = """
            INSERT INTO score_backup
                (calc_date, score)
            VALUES (%s, %s)
            ON CONFLICT (calc_date) DO NOTHING
            """
            insretado = self.db.execute_non_query(sql, [self.calc_date, round(self.to_native(score))])
            if insretado == 0:
                logger.warning("[backup_score]: No se insertaron los registros para %s: ya existen", self.calc_date)
            return score
        except (ValueError, DatabaseError) as err:
            self.db.get_connection().rollback()
            raise RuntimeError("Error al respaldar ScoreCalculator") from err

    def run(self):
        """
        1. Respalda config → devuelve config_id
        2. Respalda cada indicador
        3. Respalda score final
        """
        conn = self.db.get_connection()
        try:
            with conn:
                cfg_id = self.backup_config()
                #native_value = self.to_native(cfg_id)
                self.backup_fear_greed(cfg_id)
                self.backup_spx(cfg_id)
                self.backup_vix(cfg_id)
                final_score = self.backup_score(cfg_id)
                return {
                    "date":      self.calc_date,
                    "config_id": cfg_id,
                    "score":     final_score
                }
        except  Exception as e:
            raise

if __name__ == "__main__":
    try:
        print("✅ Respaldo completado:", ScorerBackup().run())
    except Exception as e:
        logger.error("Ocurrio un error al tratar de respaldar la información: ", e)