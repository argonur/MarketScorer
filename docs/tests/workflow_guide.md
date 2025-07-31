# Configuración para Workflow on demand

Se establece con `workflow_dispatch` y el horario de ejecucion automatico con `schedule`

- Ejemplo:

```powershell
  workflow_dispatch:
  schedule:
    - cron: "30 06 * * 2-6" # Daily at 06:30 AM UTC
```

Explicación de la sintaxis cron:

- `30 06 * * 2-6` significa:
- `30`: Minuto 30 (0 significa en punto)
- `06`: Hora 06 (6 AM en formato 24h)
- `*`: Cualquier día del mes
- `*`: Cualquier mes
- `2-6`: Días de la semana (2 = Martes, 6 = Sábado)
- GitHub Actions usa UTC por defecto

Esto nos permitirá ejecutar el workflow manualmente desde Github Actions, te aparecerá un botón que dirá `Run Workflow` junto al selector de ramas.

# Configuración de ejecucion del Workflow

Puedes configurar distintos parámetros en la ejecución del workflow.

Por ejemplo en el paso **Ejecutar pruebas y coverage** puedes personalizar a que modulo ejecutar los tests y coverage:

```yaml
# Actualmente se encuentra asi
- name: 🧪 Ejecutar pruebas y coverage
  run: |
    mkdir -p htmlcov/reports
    python tests/run_tests.py             # Ejecuta los tests de todo el sistema
    python -m core.scoreCalculator        # Ejecuta el script de scoreCalculator y muestra el resultado
```
