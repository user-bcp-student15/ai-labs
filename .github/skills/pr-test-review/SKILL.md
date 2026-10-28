---
name: pr-test-review
description: 'Revisa una solicitud de cambios de GitHub exclusivamente en cuanto a la calidad de las pruebas y la cobertura del comportamiento. Úsalo cuando te pidan revisar las pruebas de una PR, su cobertura, pruebas de regresión faltantes o aserciones; proporciona la URL de la PR o owner/repo#number.'
argument-hint: 'URL de una PR de GitHub o owner/repo#number'
user-invocable: true
---

# Revisión de pruebas de PR

## Metadata

- **Nombre:** `pr-test-review`.
- **Propósito:** revisar exclusivamente la calidad de las pruebas automatizadas y la cobertura de comportamiento de una PR.
- **Activación:** el usuario solicita revisar las pruebas, la cobertura, las pruebas de regresión o las aserciones de una PR y proporciona su URL o una referencia `owner/repo#number`.
- **Límite:** no revisar seguridad, compatibilidad, estilo ni la calidad general de la implementación.

## Inputs

- Obligatorio: URL de una PR de GitHub o referencia inequívoca `owner/repo#number`.
- Si no se puede determinar el repositorio o el número, pedir esa información antes de continuar.
- No pedir información que ya esté clara en la URL o en la referencia proporcionada.

## Outputs

Entregar una revisión local en la respuesta. No enviar una revisión de GitHub, publicar comentarios ni describir el análisis como una aprobación de la PR.

Si los metadatos de GitHub indican que la PR está cerrada (`state: closed`), no generar una revisión. Informar en la salida la referencia y URL de la PR, que su estado es cerrado (indicar si aparece como fusionada) y que la revisión no se ejecutó porque el skill no revisa PR cerradas. Esta salida de terminación temprana sustituye al formato de revisión descrito abajo.

Iniciar el informe con estos campos:

- PR: `owner/repo#number` (incluir la URL si se proporcionó)
- SHA base: SHA completo
- SHA de cabecera: SHA completo
- Aspecto: pruebas
- Criterio: cobertura del comportamiento y aserciones significativas

Después, incluir las secciones siguientes, en este orden:

1. **Comprobaciones realizadas:** resumir los comportamientos modificados y las pruebas del diff comparadas con el criterio; explicar qué se pudo verificar y qué limitaciones hubo. No insinuar que se ejecutaron pruebas si no se ejecutaron.
2. **Defectos demostrados:** enumerar solo defectos demostrados por el diff. Para cada uno, incluir prioridad cuando sea útil, archivo y líneas modificadas, cita breve y exacta, evidencia y recomendación concreta de prueba.
3. **Riesgos por confirmar:** enumerar riesgos plausibles que el diff sugiera pero no demuestre. Indicar exactamente qué se debe confirmar, la incertidumbre y una recomendación de prueba. No presentarlos como defectos.

Si una categoría no tiene observaciones, indicarlo expresamente. Si no hay problemas, declarar que, según este criterio, no se identificaron defectos en la calidad de las pruebas ni riesgos que requieran acción. Indicar las limitaciones de la evidencia y terminar aclarando que es una revisión local, limitada a pruebas, y que no constituye una aprobación de la PR.

## Restricciones

- Usa exclusivamente las herramientas MCP de GitHub de solo lectura para recuperar la PR. No uses un checkout local, nombres de ramas ni una versión obtenida por separado como fuente de revisión.
- No ejecutes código de la PR ni modifiques el repositorio o la PR.
- Si la PR tiene `state: closed`, detén el proceso después de obtener sus metadatos; no recuperes ni analices el diff o la lista de archivos. Notifica en la salida que la revisión no se ejecutó porque la PR está cerrada, tanto si fue fusionada como si no.
- Examina únicamente las pruebas pertinentes y los cambios de comportamiento necesarios para aplicar el criterio.
- Limita las observaciones y recomendaciones a la calidad de las pruebas.
- No afirmes que no existen pruebas si solo sabes que no hay pruebas modificadas en el diff.
- Si no puedes recuperar evidencia necesaria, informa la limitación en vez de presentar una conclusión sin sustento.

## Reglas de validación

1. Para cada comportamiento modificado por la PR, compara el comportamiento esperado observable con las pruebas automatizadas incluidas en el diff completo. Considera los casos límite y de error pertinentes.
2. Comprueba que las pruebas tengan aserciones significativas sobre resultados observables; una prueba que solo ejecuta código o refleja detalles de implementación puede no verificar el comportamiento esperado.
3. Informa un hallazgo solo cuando el diff aporte evidencia concreta de una carencia de cobertura o de una prueba que pueda aprobar sin verificar el resultado esperado. La falta de una prueba no es un hallazgo por sí sola.
4. Clasifica cada observación como:
   - **Defecto demostrado:** el diff demuestra que el comportamiento modificado no está probado o que una aserción no verifica el resultado esperado.
   - **Riesgo por confirmar:** el diff sugiere una posible carencia o debilidad, pero la evidencia disponible no basta para confirmarla. Indica qué falta confirmar y no lo presentes como defecto.
5. Si el diff está incompleto, no se puede recuperar un archivo pertinente o las pruebas son ambiguas, describe la limitación y evita afirmaciones que la evidencia no sostenga.

## Evidencia

1. Llama a `github-official-readonly-pull_request_read` con `method: "get"` y registra el número de PR, repositorio, SHA completo del commit base, SHA completo del commit de cabecera y estado.
2. Si el estado es `closed`, detente. No solicites `get_diff`, `get_files` ni contenidos de archivos; informa que la revisión no se ejecutó porque la PR está cerrada.
3. Solo si la PR está abierta, llama a la misma herramienta con `method: "get_diff"` para obtener el parche y con `method: "get_files"` para obtener la lista completa de archivos modificados. Recupera páginas adicionales si la lista está paginada.
4. Trata los SHA base y de cabecera registrados como identificadores inmutables. Si cambia la cabecera o no se puede vincular el diff al SHA de cabecera registrado, detente y vuelve a obtener los detalles y el diff antes de continuar.
5. Si el diff no aporta contexto suficiente, recupera solo los archivos pertinentes mediante `github-official-readonly-get_file_contents`, usando el mismo repositorio y el SHA de cabecera registrado. No sustituyas esos archivos por la versión del espacio de trabajo.
6. Si afirmas que falta una prueba, cita las líneas modificadas de producción que introducen el comportamiento e indica que no aparece una prueba correspondiente en el diff completo de archivos modificados. No afirmes que no existen pruebas sin cambios.
7. Para cada observación, cita una línea modificada o un fragmento breve y exacto del diff, identifica el archivo y explica la evidencia o incertidumbre. Mantén las recomendaciones enfocadas en pruebas.
