Ejemplo ficticio para ilustrar el formato; los datos no corresponden a una PR real.

- PR: `acme/demo#42` (https://github.com/acme/demo/pull/42)
- SHA base: `0123456789abcdef0123456789abcdef01234567`
- SHA de cabecera: `89abcdef0123456789abcdef0123456789abcdef`
- Aspecto: pruebas
- Criterio: cobertura del comportamiento y aserciones significativas

### Comprobaciones realizadas

Comparé el cambio de `calculateTotal` con las pruebas modificadas en el diff completo. La prueba invoca la función, pero no comprueba el total devuelto. No ejecuté las pruebas.

### Defectos demostrados

1. **Prioridad: media — `src/cart.spec.ts`, líneas 12-14.** El comportamiento de producción cambia en `src/cart.ts`, línea 24:

   ```diff
   + return subtotal + shipping;
   ```

   La prueba modificada solo contiene:

   ```ts
   calculateTotal(items);
   ```

   Como descarta el valor devuelto y no tiene una aserción sobre el total, puede pasar sin verificar el comportamiento introducido. Añadir una aserción del total esperado y un caso límite pertinente, por ejemplo cuando el envío es cero.

### Riesgos por confirmar

Ninguno.

Limitación: esta revisión de ejemplo se basa en el diff; no se ejecutaron las pruebas.

Esta es una revisión local limitada a la calidad de las pruebas y no constituye una aprobación de la PR.