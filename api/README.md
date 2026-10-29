# API

## Configuracion

| Variable | Requisito |
|---|---|
| `AUTH_TOKEN_SECRET` | Obligatoria en todos los entornos. Al menos 32 bytes. Debe ser el mismo valor que usa `auth`. Sin valor real en el repositorio. |

Si falta o es mas corta de 32 bytes, la aplicacion no arranca.

Las rutas protegidas aceptan `Authorization: Bearer <token>` (o el token sin prefijo) con un JWT HS256 que incluya `sub`, `role`, `iat` y `exp`. En caso contrario responden `401` con `detail` que empieza por `Invalid token: `.

## Pruebas

Desde la raiz de ai-labs: `python tools/lab.py test api`.
