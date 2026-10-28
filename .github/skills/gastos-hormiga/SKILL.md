---
name: gastos-hormiga
description: "Usar cuando el usuario solicite analizar un Excel de presupuesto, revisar gastos fuera de presupuesto, comparar meses o generar consejos de ahorro en HTML."
argument-hint: "Ruta del Excel y mes opcional"
user-invocable: true
disable-model-invocation: true
---

# Análisis de gastos fuera de presupuesto

Usa este flujo solo cuando el usuario invoque esta skill o pida explícitamente el análisis.

1. Solicita el Excel o su ruta si no está disponible. Identifica la hoja, el presupuesto y la sección “Gastos fuera”; no supongas nombres de columnas.
2. Lee el libro sin modificarlo ni ejecutar macros. Si fechas, moneda o importes no son claros, pregunta; no inventes datos.
3. Compara los gastos fuera de presupuesto de los meses disponibles. Resalta el mes más reciente frente al anterior y señala si algún mes está incompleto.
4. Considera “gasto hormiga” solo con el criterio del libro o del usuario. Si no hay límite, presenta los gastos pequeños y repetidos como candidatos, no como una clasificación definitiva.
5. Genera un HTML independiente en español con resumen, detalle de gastos extra, comparativo mensual y sugerencias de ahorro basadas en importes y frecuencia. Explica brevemente la evidencia; no supongas que un gasto es prescindible solo por su descripción.
6. Guarda el HTML en una ubicación indicada por el usuario. Si no la indica, pregunta antes de guardar. No sobrescribas archivos existentes ni guardes datos financieros en el repositorio.
7. Conserva el Excel original. No subas información a servicios externos, no uses MCP para transmitirla y no instales dependencias ni cambies archivos del proyecto.

Si no puedes leer el Excel con las herramientas disponibles, explica la limitación y solicita una exportación CSV; no afirmes que analizaste el archivo.
