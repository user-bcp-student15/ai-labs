# HU-01 — Token firmado con expiración y claims mínimos

## Summary
- Completar el token de `POST /auth/login` con los claims `sub`, `client`, `iat` y `exp`, una expiración coherente con `expiresIn` y una política segura para `AUTH_TOKEN_SECRET`.
- La solución debe validar `client` y evitar registrar tokens o secretos. No se especifica una métrica de impacto de negocio.

## Scope
- **Dentro del alcance**
  - Añadir y verificar los claims mínimos requeridos.
  - Obtener `client` de la solicitud, validarlo y reflejarlo en el token.
  - Alinear `expiresIn` con `exp - now` dentro de una tolerancia documentada.
  - Definir el manejo del secreto y evitar su exposición en logs.
  - Probar login válido, credenciales inválidas y token expirado.
  - Documentar la decisión entre mantener HMAC o adoptar una librería JWT.
- **Fuera del alcance**
  - La HU no declara exclusiones explícitas; no se infieren cambios de contrato, migraciones de consumidores ni cambios de infraestructura.

## Supuestos
- Se toma como contexto el endpoint y los campos de respuesta indicados: `token`, `expiresIn` y `user`; el servicio usa HMAC y lee `AUTH_TOKEN_SECRET`.
- No se asumen tipos o unidades de los claims, formato permitido de `client`, valor de tolerancia ni códigos de error.
- Las pruebas y evidencias usarán valores ficticios; no incluirán secretos ni tokens reales.

## Decisiones técnicas por tomar (pendientes o resueltas)
- **Pendiente:** mantener HMAC o adoptar una librería JWT; documentar la opción elegida.
- **Pendiente:** definir el origen, formato y validación de `client`, incluido el comportamiento ante ausencia o valor inválido.
- **Pendiente:** definir tipos/unidades para `iat` y `exp`, la unidad de `expiresIn` y la tolerancia de comparación.
- **Pendiente:** definir qué entornos cuentan como laboratorio y si el servicio debe fallar al no recibir `AUTH_TOKEN_SECRET` fuera de ellos.
- **Pendiente:** confirmar compatibilidad requerida para consumidores actuales y el contrato de error para credenciales inválidas y tokens expirados.

## Riesgos y mitigaciones
- **Incompatibilidad de consumidores:** claims o cambios en la respuesta podrían afectar clientes existentes. Inventariar el contrato y sus consumidores; cubrir la respuesta actual y los cambios acordados con pruebas funcionales.
- **`client` no confiable:** un valor no validado podría quedar incorporado al token. Definir reglas de validación antes de implementar y probar valores válidos e inválidos.
- **Secreto por defecto fuera del laboratorio:** una configuración accidental podría permitir firmar tokens con una clave conocida. Acordar la política por entorno y probar la configuración sin imprimir ni incluir el secreto.
- **Expiración incoherente o exposición en logs:** comparar con reloj controlado usando la tolerancia documentada y comprobar que los logs no contienen tokens ni secretos.

## Criterios de aceptación (medibles)
- Todo token emitido tras un login válido contiene `sub`, `client`, `iat` y `exp`, y su firma se verifica con la estrategia técnica elegida.
- El claim `client` coincide con el valor validado recibido en la solicitud; un valor inválido no produce un login exitoso.
- `expiresIn` coincide con `exp - now` dentro de la tolerancia documentada, comprobado con una prueba de reloj controlado.
- Hay pruebas para login válido, credenciales inválidas y validación de un token expirado; cada una comprueba el resultado según el contrato acordado.
- Las pruebas de logging no encuentran el token ni el secreto en los registros generados con valores ficticios.
- La política de `AUTH_TOKEN_SECRET` por entorno y la decisión HMAC/JWT quedan documentadas y cubiertas por comprobaciones de configuración.

## Plan de validación
- **Pruebas unitarias**
  - Verificar claims obligatorios, correspondencia del `client`, firma y cálculo de expiración.
  - Cubrir valores inválidos de `client` y los límites temporales definidos.
- **Pruebas funcionales**
  - Probar login válido y credenciales inválidas mediante el contrato existente de `POST /auth/login`.
  - Comprobar que la validación rechaza un token expirado en el punto de verificación correspondiente.
- **Seguridad (comprobaciones mínimas)**
  - Confirmar que no se registran tokens ni secretos.
  - Verificar el comportamiento de configuración del secreto en los entornos acordados, usando solo valores ficticios.
  - Revisar que `client` se valida antes de incorporarse al token.
- **Evidencia requerida (qué adjuntar)**
  - Esta ficha derivada de HU-01 y la decisión técnica documentada.
  - Salida de las pruebas de claims, expiración y errores de autenticación.
  - Documentación de `AUTH_TOKEN_SECRET` por entorno, sin valores secretos.
  - Evidencia de revisión de logs redactados con datos ficticios.

## Tareas sugeridas por rol
- **Chapter/PO**
  - Confirmar qué identifica `client` y qué valores debe aceptar.
  - Acordar el comportamiento esperado para `client` ausente o inválido.
  - Confirmar compatibilidad de los consumidores y el resultado funcional esperado para errores.
- **Tech Lead**
  - Resolver y documentar HMAC frente a librería JWT.
  - Definir semántica y unidades de claims, `expiresIn` y tolerancia temporal.
  - Acordar política del secreto por entorno y estrategia de compatibilidad.
- **Backend**
  - Emitir los claims acordados y validar `client` antes de firmar.
  - Mantener `expiresIn` coherente con `exp` según la tolerancia aprobada.
  - Añadir pruebas para login, expiración, configuración del secreto y ausencia de datos sensibles en logs.
- **Frontend**
  - Confirmar si el cliente de login debe enviar `client`; realizar el ajuste solo después de acordar el campo y sus valores.
  - Verificar que el consumo de `token`, `expiresIn` y `user` sigue el contrato acordado.
  - Evitar registrar el token o el secreto en logs del cliente.
- **QA**
  - Ejecutar casos de login válido e inválido y validación de token expirado.
  - Verificar claims, cálculo de expiración y límites con los valores definidos.
  - Adjuntar resultados de pruebas y revisión de logs/configuración sin secretos reales.
- **Cyber**
  - Revisar la estrategia de firma y el manejo del secreto por entorno.
  - Comprobar la validación de `client` y la ausencia de tokens/secretos en logs.

## Preguntas abiertas
- ¿Qué representa `client`, de dónde procede y qué formato/valores se consideran válidos?
- ¿Qué tipos y unidades se usarán para `iat`, `exp` y `expiresIn`? ¿Cuál es la tolerancia temporal?
- ¿Qué entornos se consideran laboratorio y qué debe ocurrir si falta el secreto en cada entorno?
- ¿Se requiere mantener compatibilidad con tokens ya emitidos o consumidores existentes?
- ¿Qué respuesta concreta corresponde a credenciales inválidas y a tokens expirados según el contrato actual?
- ¿Qué consumidor valida el token expirado y dónde debe comprobarse ese caso?
