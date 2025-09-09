- Este modulo proporciona funcionalidades para determinar el estado actual del mercado, Zona horaria de Nueva York por defecto.

- Calcula el ultimo cierre hábil
- Esta diseñado para integrarse en módulos que requieran decisiones basadas en la disponibilidad del mercado, como consultas de precios.

---

# Funcionalidades Principales

| Función                          | Descripción                                                         |
| -------------------------------- | ------------------------------------------------------------------- |
| `market_now`                     | Normaliza un datetime a la zona horaria del mercado                 |
| `is_market_open`                 | Devueve `True` o `False` dependiendo del estatus actual del mercado |
| `get_market_today`               | Devuelve la fecha actual en la zona horaria del mercado             |
| `get_last_trading_date`          | Calcula la ultima fecha hábil con el cierre valido                  |
| `get_last_trading_close`         | Devuelve el datetime exacto del ultimo cierre hábil                 |
| `yfinance_window_for_last_close` | Genera un rango de fechas para consultas en APIs como yfinance.     |

---

## Zona horaria consistente

Se utiliza `Zoneinfo("America/New_York")` para asegurar que todas las operaciones se alineen con el horario oficial de NYSE.

### Manejo de fechas y horas

Las funciones distinguen entre `naive` y `aware` garantizando precisión en entornos distribuidos.

### Lógica de cierre hábil

- Si es fin de semana retrocede, hasta el viernes.
- Si es día hábil pero antes del cierre, considera el día anterior.
- Si ya paso el cierre considera el día actual.
- No se consideran días feriados

---

Las funciones aceptan parámetros opcionales **(now, tz, market_open, marker_close)**, para facilitar pruebas y adaptaciones.

```python
from data.market_dates import is_market_open, get_last_trading_close

if is_market_open():
    print("El mercado está abierto.")
else:
    print("El mercado está cerrado.")

print("Último cierre:", get_last_trading_close())
```
