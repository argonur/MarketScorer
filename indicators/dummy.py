from IndicatorModule import IndicatorModule

class Dummy(IndicatorModule):

    def fetch_data(self):
        pass
    
    def normalize(self):
        return None
    
    def get_score(self):
        return "Dummy sobrescrito"

    # Intenta crear una instancia de la clase dummy
try:
    dummy = Dummy()
    print("¡Éxito! La clase dummy implementa todos los métodos abstractos.")
    
    # Verificación adicional de métodos
    print("Método abstracto 1:", dummy.fetch_data())  # None (por el pass)
    print("Método abstracto 2:", dummy.normalize())  # None
    print("Método opcional:", dummy.get_score())  # Usa la implementación base o la sobrescrita
    
except TypeError as e:
    print(f"Error: {e}\nLa clase dummy NO implementa todos los métodos abstractos.")