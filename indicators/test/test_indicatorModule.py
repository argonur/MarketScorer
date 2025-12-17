import pytest
from abc import ABC, abstractclassmethod
from indicators.IndicatorModule import IndicatorModule
from datetime import date

# Pruebas que aplican a TODAS las clases que implementan la interfaz
class TestIndicatorModuleInterface:
    """ Pruebas para cualquier implementacion de IndicatorModule. """
    @pytest.fixture
    def implementation(self, indicator_instance):
        return indicator_instance
    
    def test_has_fetch_data(self, implementation):
        assert hasattr(implementation, 'fetch_data')
        assert callable(implementation.fetch_data)
    
    def test_has_normalize(self, implementation):
        assert hasattr(implementation, 'normalize')
        assert callable(implementation.normalize)

    def test_override_get_score(self, implementation):
        assert hasattr(implementation, 'get_score')
        assert callable(implementation.get_score)
    def test_get_score_returns_normalized_value(self, implementation):
        fecha = date(2025, 12, 15)
        score = implementation.get_score(fecha)
        assert score == implementation.normalize(fecha)

    # La interfaz no permite ser instanciada directamente
    def test_interface_cannot_be_instantiated(self):
        from indicators.IndicatorModule import IndicatorModule
        with pytest.raises(TypeError):
            IndicatorModule()
    
    def test_subclass_implements_all_required_methods(self, implementation):
        assert isinstance(implementation, IndicatorModule)
