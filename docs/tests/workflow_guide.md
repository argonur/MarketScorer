# Configuración para Workflow on demand

Se establece con `workflow_dispatch` y el horario de ejecucion automatico con `schedule`

- Ejemplo:

```powershell
  workflow_dispatch:
  schedule:
    - cron: "0 12 * * 1-5" # Daily at 12:00 UTC Lunes a Viernes
```

Esto nos permitirá ejecutar el workflow manualmente desde Github Actions, te aparecerá un botón que dirá `Run Workflow` junto al selector de ramas.

# Configuración de ejecucion del Workflow

Puedes configurar distintos parámetros en la ejecución del workflow.

Por ejemplo en el paso **Ejecutar pruebas y coverage** puedes personalizar a que modulo ejecutar los tests y coverage:

```yaml
# Actualmente se encuentra asi
      - name: 🧪 Ejecutar pruebas y coverage
        run: |
          mkdir -p htmlcov/reports
          python tests/run_tests.py indicators/ # Puedes modificar esta linea por:
          
			    python tests/run_test.py core/       # Ejecuta test y coverage del paquete core
			    python tests/run_test.py           # Ejecuta test y coverage de todo el sistema
```