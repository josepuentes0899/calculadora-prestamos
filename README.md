# Calculadora de Préstamos

Página web para calcular la cuota mensual de un préstamo y ver su tabla de pagos (amortización).

## Uso

Abre `index.html` en cualquier navegador. No requiere instalación ni conexión a internet.

1. Ingresa el **monto**, la **tasa de interés anual (%)** y el **plazo** (en meses o años).
2. Pulsa **Calcular** para ver:
   - Cuota mensual, total de intereses, total a pagar y número de pagos.
   - La tabla de pagos con cuota, capital, interés y saldo de cada mes.
3. Opcional: descarga la tabla con **Descargar CSV**.

## Cálculo

Se usa cuota fija (sistema francés):

```
cuota = P · r / (1 − (1 + r)^−n)
```

donde `P` es el monto, `r` la tasa anual / 12 y `n` el número de meses. Con tasa 0 %, la cuota es `P / n`.
Los montos se redondean a centavos y la última cuota se ajusta para dejar el saldo exactamente en 0.
