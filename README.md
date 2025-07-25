# MarketScorer

## Requisitos previos

Antes de comenzar a desarrollar o ejecutar test de nuestro proyecto debemos:

1. Crear un entorno virtual (donde se instalaran las dependencias que necesita el proyecto)

```bash
python3 -m venv venv  # Esto crea un entorno llamado "venv"
```

2. Activar el entorno virtual

```bash
source venv/bin/activate
# Tu terminal mostrará algo como: (venv) usuario@macbook ...
```

3. Instalar las dependencias desde requirements.txt con el comando:

```bash
pip install -r requirements.txt
```

# Ejecutar tests, coverage y reporte HTML

- Para ejecutar tests y coverage de todo el sistema ejecutar el siguiente comando desde la raíz del proyecto:

```bash
python3 tests/run_tests.py
```

- Para ejecutar tests, coverage y reporte de un paquete en especifico

```bash
python3 test/run_tests.py /indicators
# Este comando ejecutara todos los tests dentro del paquete
```

- Para ejecutar los tests y coverage _(`pytest`)_ de una clase en especifico ejecute el siguiente comando:

```python3
pytest indicators/tests/test_fear_greed_indicator.py -v --cov=indicators.FearGreedIndicator --cov-report=term-missing
```

Solo asegurate de indicar corretamente la ruta de las pruebas de tu clase

### Resultado

Se espera un resultado similar en tu terminal.

- Prueba para el paquete indicators

```powershell
▶ Ejecutando pruebas en: indicators

================================================= test session starts ==================================================
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0
rootdir: /home/osvaldo/github/MarketScorer
plugins: html-4.1.1, cov-6.2.1, metadata-3.1.1
collected 7 items

indicators/test/test_dummy.py ....                                                                               [ 57%]
indicators/test/test_indicatorModule.py ...                                                                      [100%]

==================================================== tests coverage ====================================================
___________________________________ coverage: platform linux, python 3.12.3-final-0 ____________________________________

Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
indicators/IndicatorModule.py                10      2    80%
indicators/__init__.py                        0      0   100%
indicators/dummy.py                           8      0   100%
indicators/test/__init__.py                   0      0   100%
indicators/test/conftest.py                   5      0   100%
indicators/test/test_dummy.py                15      0   100%
indicators/test/test_indicatorModule.py      16      0   100%
-------------------------------------------------------------
TOTAL                                        54      2    96%
Coverage HTML written to dir htmlcov
Required test coverage of 90% reached. Total coverage: 96.30%
================================================== 7 passed in 0.06s ===================================================
```

- Prueba para una clase en especifico

```powershell
❯ pytest indicators/test/indicators/test_fear_greed_indicator.py -v --cov=indicators.FearGreedIndicator
=================================================================== test session starts ====================================================================
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /home/osvaldo/github/MarketScorer/marketScorer/bin/python3
cachedir: .pytest_cache
metadata: {'Python': '3.12.3', 'Platform': 'Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39', 'Packages': {'pytest': '8.4.1', 'pluggy': '1.6.0'}, 'Plugins': {'html': '4.1.1', 'cov': '6.2.1', 'metadata': '3.1.1'}}
rootdir: /home/osvaldo/github/MarketScorer
plugins: html-4.1.1, cov-6.2.1, metadata-3.1.1
collected 18 items

indicators/test/indicators/test_fear_greed_indicator.py::test_fetch_data_valida PASSED                                                               [  5%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_valido PASSED                                                                [ 11%]
indicators/test/indicators/test_fear_greed_indicator.py::test_fetch_data_error PASSED                                                                [ 16%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_falla PASSED                                                                 [ 22%]
indicators/test/indicators/test_fear_greed_indicator.py::test_valores_fuera_de_rango_lanza_excepcion[-70] PASSED                                     [ 27%]
indicators/test/indicators/test_fear_greed_indicator.py::test_valores_fuera_de_rango_lanza_excepcion[-1] PASSED                                      [ 33%]
indicators/test/indicators/test_fear_greed_indicator.py::test_valores_fuera_de_rango_lanza_excepcion[-25] PASSED                                     [ 38%]
indicators/test/indicators/test_fear_greed_indicator.py::test_valores_fuera_de_rango_lanza_excepcion[105] PASSED                                     [ 44%]
indicators/test/indicators/test_fear_greed_indicator.py::test_valores_fuera_de_rango_lanza_excepcion[125] PASSED                                     [ 50%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_con_valores_invalidos[-1] PASSED                                             [ 55%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_con_valores_invalidos[101] PASSED                                            [ 61%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_con_valores_invalidos[None] PASSED                                           [ 66%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_parametrizado[75-0.75] PASSED                                                [ 72%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_parametrizado[55-0.55] PASSED                                                [ 77%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_parametrizado[25-0.25] PASSED                                                [ 83%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_parametrizado[20-0.2] PASSED                                                 [ 88%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_parametrizado[100-1.0] PASSED                                                [ 94%]
indicators/test/indicators/test_fear_greed_indicator.py::test_normalize_parametrizado[0-0.0] PASSED                                                  [100%]

====================================================================== tests coverage ======================================================================
_____________________________________________________ coverage: platform linux, python 3.12.3-final-0 ______________________________________________________

Name                               Stmts   Miss  Cover
------------------------------------------------------
indicators/FearGreedIndicator.py      21      0   100%
------------------------------------------------------
TOTAL                                 21      0   100%
==================================================================== 18 passed in 0.05s ====================================================================
```
