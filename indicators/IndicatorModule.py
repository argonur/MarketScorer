from abc import ABC, abstractmethod
class IndicatorModule(ABC):
    """
    Clase abstracta para todos los indicadores.
    Es la interfaz que deben implementar.
    """

    @abstractmethod
    def fetch_data(self):
        """ Obtiene los datos necesarios para el indicador. """
    pass

    @abstractmethod
    def normalize(self):
        """ 
        - Procesa los datos obtenidos y los transforma en valores entre 0 y 1.
        - Este valor representa la contribución del indicador al sistema.
        """
    pass

    def get_score(self):
        """ 
        - Retorna el valor normalizado.
        - Este metodo puede ser sobreescrito si el indicador necesita ajustar el resultado.
        """
        return self.normalize()