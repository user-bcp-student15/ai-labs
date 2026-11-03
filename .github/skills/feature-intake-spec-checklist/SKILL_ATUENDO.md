---
name: daily-work-outfit
description: Recomienda un atuendo diario para ir al trabajo considerando el clima disponible, el código de vestimenta, las actividades del día y las prendas que la persona tiene.
---

# Skill: Daily Work Outfit

## 1) Metadata
- **Skill ID:** daily-work-outfit
- **Version:** 0.1.0
- **Purpose:** Ayudar a seleccionar un atuendo práctico y apropiado para ir al trabajo según las condiciones y preferencias indicadas por la persona.
- **Audience (roles):** Persona usuaria; opcionalmente, asistente de estilo personal.
- **When to use:** Antes de vestirse para una jornada laboral o cuando se necesite preparar atuendos para varios días de trabajo.
- **When NOT to use:** Para definir uniformes oficiales sin consultar la política de la organización, ni para sustituir requisitos de seguridad laboral o equipo de protección.
- **Sensitive inputs:** No solicites ni incluyas datos personales innecesarios. No necesitas dirección exacta, credenciales ni información confidencial del empleador. Una ubicación general puede ser suficiente si se consulta el clima.
- **Expected output:** Markdown estructurado mediante la sección Output a continuación.

## 2) Inputs
Solicita o utiliza la información disponible en este formato:
- **Fecha o jornada:** (hoy, mañana o fecha específica)
- **Clima:** (pronóstico o condiciones conocidas; si no está disponible, indicarlo)
- **Ubicación general:** (opcional; solo si hace falta consultar el clima)
- **Código de vestimenta:** (formal, business casual, casual, uniforme u otro)
- **Actividades del día:** (reuniones, trabajo de oficina, visitas, desplazamientos, eventos)
- **Prendas disponibles:** (opcional; prendas, calzado y abrigo que la persona tiene)
- **Preferencias y comodidad:** (colores, estilo, tejidos, prendas que prefiere evitar)
- **Restricciones prácticas:** (presupuesto si se propone comprar algo, movilidad, tiempo para cambiarse u otras necesidades relevantes)

Si falta información crítica para recomendar un atuendo apropiado —por ejemplo, el código de vestimenta cuando hay una reunión formal—, pregunta antes de concluir. Si faltan datos no críticos, declara el supuesto o presenta una recomendación provisional claramente identificada.

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Atuendo recomendado**
   - Parte superior
   - Parte inferior
   - Calzado
   - Capa exterior o accesorios, si aplican

2. **Por qué funciona**
   - Adecuación al código de vestimenta y a las actividades
   - Consideración del clima disponible
   - Comodidad y practicidad

3. **Alternativa**
   - Una opción distinta usando las prendas conocidas, si hay información suficiente

4. **Qué falta confirmar**
   - Datos desconocidos que podrían cambiar la recomendación; si no hay, indicar “Nada importante”

5. **Preparación rápida**
   - Una comprobación práctica antes de salir, como revisar el clima o confirmar si se requiere uniforme

## 4) Constraints
- No inventes prendas que la persona no haya indicado como disponibles. Si no proporciona un guardarropa, recomienda tipos de prendas de forma genérica y acláralo.
- No inventes el clima ni afirmes haber consultado un pronóstico si no se ha consultado una fuente disponible.
- Respeta el código de vestimenta y las actividades laborales indicadas.
- Si existe un uniforme obligatorio o un requisito de seguridad laboral, priorízalo sobre las preferencias de estilo.
- No recomiendes compras como requisito; si sugieres una compra opcional, explica por qué y respeta el presupuesto indicado.
- No hagas juicios sobre el cuerpo, la edad, el género o la apariencia de la persona. No asumas género ni preferencias por estereotipos.
- Si falta información crítica, detente y pregunta; no inventes detalles para completar la recomendación.
- Mantén la respuesta breve, práctica y fácil de aplicar antes de salir al trabajo.

## 5) Validation Rules
La salida es válida si:
- Incluye todas las secciones definidas en Output.
- Recomienda un atuendo completo o indica claramente qué dato crítico falta para hacerlo.
- Tiene en cuenta el código de vestimenta y las actividades laborales proporcionadas.
- No presenta datos meteorológicos desconocidos como hechos.
- No inventa prendas disponibles ni reglas del lugar de trabajo.
- Incluye una alternativa cuando la información permite proponerla; si no, explica por qué no aplica.
- No contiene datos personales innecesarios ni recomendaciones basadas en estereotipos.
- Identifica explícitamente cualquier supuesto que afecte a la recomendación.

## 6) Evidence
Conserva o referencia estos elementos si el Skill se incorpora a un repositorio o se evalúa:
- `SKILL.md` versionado.
- `examples/input.sample.atuendo.md`.
- `examples/output.sample.atuendo.md`.
- Tag de versión para el Skill, como `skill-daily-work-outfit-v0.1.0`.
- Para validar una recomendación concreta, conserva la entrada utilizada y la salida generada, sin incluir datos personales innecesarios.