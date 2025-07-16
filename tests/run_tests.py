import sys
import subprocess

def run_tests(target='.', html=True):
    """Ejecuta pytest con cobertura, ya sea para un paquete o para todo el sistema."""
    
    cmd = [
        "pytest",
        target,
        f"--cov={target}",
        "--cov-fail-under=90",
        "--cov-report=term",           # Reporte en consola
    ]

    if html:
        cmd.append("--cov-report=html")  # Reporte HTML si se desea

    print(f"\n▶ Ejecutando pruebas en: {target}\n")
    subprocess.run(cmd)


if __name__ == "__main__":
    # Lee argumentos de línea de comandos
    if len(sys.argv) > 1:
        paquete = sys.argv[1]
    else:
        paquete = "."  # Todo el sistema por defecto

    run_tests(target=paquete)
