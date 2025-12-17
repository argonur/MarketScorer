from abc import ABC, abstractmethod
from datetime import date
class IndicatorModule(ABC):
    """
    Clase abstracta para todos los indicadores.
    Es la interfaz que deben implementar.
    """

    @abstractmethod
    def fetch_data(self, date: date):
        """ Obtiene los datos necesarios para el indicador. """
    pass

    @abstractmethod
    def normalize(self, date: date):
        """ 
        - Procesa los datos obtenidos y los transforma en valores entre 0 y 1.
        - Este valor representa la contribución del indicador al sistema.
        """
    pass

    def get_score(self, date: date):
        """ 
        - Retorna el valor normalizado.
        - Este metodo puede ser sobreescrito si el indicador necesita ajustar el resultado.
        """
        return self.normalize(date)

    def get_last_close(self):
        """
        - Metodo para obtener el valor del ultimo cierre de un simbolo.
        - Utiliza yfinance para descargar los datos.
        - Retorna el valor del cierre o None si no se obtuvieron datos.
        """
    pass