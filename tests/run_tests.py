import sys
import subprocess

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
    subprocess.run(cmd)

# Constructor el cual nos permite pasarle un target path individual a testear desde la terminal
if __name__ == "__main__":
    # Lee argumentos de línea de comandos
    if len(sys.argv) > 1:
        paquete = sys.argv[1]
    else:
        paquete = "."  # Todo el sistema por defecto

    run_tests(target=paquete)
