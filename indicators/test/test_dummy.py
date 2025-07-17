from indicators.dummy import Dummy
from indicators.IndicatorModule import IndicatorModule
import pytest

class TestDummyImplementation:
    """Pruebas específicas para la implementación Dummy"""
    
    @pytest.fixture
    def dummy(self):
        return Dummy()
    
    def test_instance_creation(self, dummy):
        assert isinstance(dummy, IndicatorModule)

    def test_fetch_data_implementation(self, dummy):
        assert dummy.fetch_data() is None

    def test_fetch_data_idempotent(self, dummy):
        assert dummy.fetch_data() == dummy.fetch_data()
    
    def test_normalize_implementation(self, dummy):
        assert dummy.normalize() is None
    
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

