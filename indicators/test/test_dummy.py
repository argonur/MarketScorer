from indicators.dummy import Dummy
from indicators.IndicatorModule import IndicatorModule
import pytest

class TestDummyImplementation:
    """Pruebas específicas para la implementación Dummy"""
    
    @pytest.fixture
    def dummy(self):
        return Dummy()

    def test_fetch_data_implementation(self, dummy):
        assert dummy.fetch_data() is None
    
    def test_normalize_implementation(self, dummy):
        assert dummy.normalize() is None
    
    def test_optional_method_override(self, dummy):
        assert dummy.get_score() == "Dummy sobrescrito"
    
    def test_instance_creation(self, dummy):
        assert isinstance(dummy, IndicatorModule)
