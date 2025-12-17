from indicators.dummy import Dummy
from indicators.IndicatorModule import IndicatorModule
import pytest
from datetime import date

class TestDummyImplementation:
    """Pruebas específicas para la implementación Dummy"""
    
    @pytest.fixture
    def dummy(self):
        return Dummy()
    
    def test_instance_creation(self, dummy):
        assert isinstance(dummy, IndicatorModule)

    def test_fetch_data_implementation(self, dummy):
        fecha = date(2025, 12, 15)
        assert dummy.fetch_data(fecha) is None

    def test_fetch_data_idempotent(self, dummy):
        fecha = date(2025, 12, 15)
        assert dummy.fetch_data(fecha) == dummy.fetch_data(fecha)
    
    def test_normalize_implementation(self, dummy):
        fecha = date(2025, 12, 15)
        assert dummy.normalize(fecha) is None
    
    def test_instance_creation(self, dummy):
        assert isinstance(dummy, IndicatorModule)

    def test_dummy_is_subclass_of_interface(self):
        assert issubclass(Dummy, IndicatorModule)


    def test_dummy_implements_all_abstract_methods(self):
        try:
            dummy = Dummy()
            assert isinstance(dummy, IndicatorModule)
        except TypeError as e:
            pytest.fail(f"La clase Dummy no implementa todos los métodos abstractos: {e}")

