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
python test/run_tests.py paquete_individuals
```

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
