import sys
import os
import subprocess
import argparse

def run_tests(target='.'):
    """Ejecuta pytest con cobertura, ya sea para un paquete o para todo el sistema."""
    
    cmd = [
        "pytest",
        target,
        f"--cov={target}",
        "--cov-fail-under=70",                                  # Umbral de coverage
        "--cov-branch",                                         # Cobertura de ramas logicas: if, try, etc.
        "--cov-report=xml:htmlcov/reports/coverage.xml",        # Reporte XML para CI
        "--cov-report=html:htmlcov/reports/coverage_html",      # directorio para reporte HTML
        "--html=htmlcov/reports/tests.html",                    # este es el HTML de pruebas
        "--self-contained-html",
        "--cov-report=term",                                    # Reporte en consola
        "--cov-report=term-missing",                            # Mostrar lineas no cubiertas
    ]

    print(f"\n▶ Ejecutando pruebas en: {target}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"❌ Las pruebas fallaron o la cobertura está por debajo del 70%")
        sys.exit(result.returncode)
    print("✅ Pruebas completadas con éxito y cobertura suficiente.")

# Constructor el cual nos permite pasarle un target path individual a testear desde la terminal
if __name__ == "__main__":
    # Agrega la raíz del proyecto al sys.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Paquete o archivo de tests a ejecutar", nargs='?', default='.')
    args = parser.parse_args()

    run_tests(target=args.target)
