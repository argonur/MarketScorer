import pytest
from abc import ABC, abstractclassmethod

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
        assert implementation.get_score() is not None