# Documentación para el Usuario

## 1. Indicators

Contiene configuraciones especificas de cada indicador que el sistema MarketScorer interpreta o monitorea.

Cada indicador se define por su nombre `(Por ejemplo S&P 500 = 'spx')` seguido de parametros que definen su comportamiento esperado.

- Ejemplo para `spx`:

```python
"spx": {
  "lower_ratio": -0.2,
  "upper_ratio": 0.2
}
```

- `lower_ratio`: Ratio mínimo permitido (-20% en este caso)
- `upper_ratio`: Ratio máximo permitido (+20%)

<aside>
👉🏼 Impacto

Si el calculo para el índice S&P 500 con relación a su Simple Moving Average (SMP200) cae por debajo de `lower_ratio` o supera el `upper_ratio` el sistema tomara decisiones basadas en este indicador.

</aside>

---

## 2. Weights

Define el peso relativo de cada indicador en los calculos globales del sistema (por ejemplo: scoreCalculator).

Los pesos deben estar definidos entre 0.0 y 1.0, pero la suma total de los pesos de los indicadores debe sumar 1.0 obligatoriamente.

```python
"weights": {
  "fear_greed": 1.0
}
# Por el momento solo se ha implementado un solo peso para un indicador fear_greed
```

- `fear_greed` : Indicador que representa el nivel de animo al riesgo del mercado
- Valor `1.0`: Representa el peso del indicador en el sistema, actualmente tiene el peso completo sobre las decisiones.
- La suma de todos los pesos es de `1.0` como requiere el sistema.

---

## 3. Backtesting

Controla el periodo historico sobre el cual se ejecutan pruebas restrospectivas del sistema.

Debe contener dos fechas validas en formato `YYYY-MM-DD`

```python
"backtesting": {
  "start_date": "2010-01-01",
  "end_date": "2023-12-31"
}
```

- `start_date`: Fecha de inicio del análisis
- `end_date`: Fecha de fin del análisis

<aside>
👉🏼 Impacto

Define el periodo sobre el cual se ejecutaran simulaciones históricas para validar el rendimiento del sistema.

</aside>
