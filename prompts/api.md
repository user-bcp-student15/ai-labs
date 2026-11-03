###ÁMBITO

Workspace ai-labs abierto en su raíz. Lee código solo en api/.

Todas las rutas parten de la raíz. Lee README.md, RETO.md y docs/ generales como contexto.

Este pedido es de solo lectura; no escribas ni modifiques archivos.

Git se ejecuta desde la raíz; las pruebas propuestas usan cwd api/.

No leas ni modifiques código de auth/ ni web/. Usa IDs H-API-NN y componente api.

###CONTEXTO

El componente api/ utiliza FastAPI para exponer los datos y operaciones del sistema.

La documentación interactiva está disponible en http://localhost:8000/docs, si el servicio está levantado.

Lee docs/ENDPOINTS.md si existe. No des por cierta la lista de endpoints de RETO.md: contrástala con el código implementado.

Localiza el punto de entrada, los routers, modelos Pydantic, validaciones y recorrido hacia los servicios y acceso a datos.

###OBJETIVO

Determinar si los endpoints de FastAPI implementan correctamente sus contratos HTTP, identificando inconsistencias entre rutas, métodos, entradas, validaciones, operaciones y respuestas.

###RESTRICCIONES
No edites archivos ni modifiques código.
No ejecutes ataques contra servicios remotos.
Utiliza únicamente código y datos ficticios locales.
No asumas que /docs está disponible; compruébalo antes de consultarlo.
No ejecutes operaciones que puedan modificar o eliminar datos reales.
No inspecciones otros componentes.
Distingue entre comportamiento observado, comprobado e hipótesis.
Si falta un archivo o no puedes verificar algo, indícalo.
No afirmes que una prueba pasó si solamente la propusiste.

###CRITERIOS DE ACEPTACIÓN
Identifica el punto de entrada de FastAPI y los endpoints, con archivo y línea.
Relaciona cada endpoint con su método HTTP, parámetros y modelos de entrada y salida.
Describe el recorrido desde la solicitud HTTP hasta la operación correspondiente.
Verifica las validaciones, códigos HTTP y manejo de errores según el código observado.
Contrasta los endpoints documentados con los realmente implementados.
Propón pruebas locales no destructivas para solicitudes válidas, datos incorrectos, parámetros ausentes, recursos inexistentes y métodos no permitidos.
Indica para cada prueba los datos ficticios y el resultado esperado según el contrato observado.

###FORMATO DE RESPUESTA

Presenta los hallazgos en una tabla:

| ID | Afirmación | Evidencia archivo:línea | Estado (comprobado/hipótesis/no comprobado) | Prueba propuesta |

Organiza los hallazgos por:

Inicialización y rutas.
Validaciones y modelos.
Lógica de negocio y acceso a datos.
Respuestas HTTP y errores.
Diferencias con la documentación.

Finaliza con:

Cobertura de endpoints

Resumen de rutas, métodos y estado de verificación.

Preguntas abiertas

Dudas pendientes de resolver.

Comandos no ejecutados

Comandos necesarios para completar las comprobaciones y qué verificarían.

Indica también las limitaciones del análisis y los archivos que no pudieron verificarse.