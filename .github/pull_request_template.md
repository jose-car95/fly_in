## Resumen

<!-- Qué cambia y por qué, en 2-3 frases. -->

Closes #

## Alcance del slice

- [ ] Es un slice vertical único y delimitado (ver `docs/PLAN.md`).
- [ ] No adelanta alcance de milestones posteriores.
- [ ] Decisiones/ambigüedades nuevas quedan registradas en `docs/SPEC_NOTES.md` o `docs/PROGRESS.md`.

## Comportamiento y criterios de aceptación

<!-- Ejemplos concretos entrada -> salida. Enlaza el/los test(s) que lo prueban. -->

## Diseño: clases, flujo y trade-off

<!-- Clases nuevas/tocadas y su responsabilidad. Flujo de datos. El trade-off clave de
     esta decisión de diseño (el "Teaching" del slice, en español). -->

## Invariantes de Fly-In afectados

<!-- Marca solo los que aplican a este slice; el resto se deja sin marcar. -->

- [ ] OOP + type-safe: `mypy .` y `flake8 .` limpios, sin `Any` innecesario.
- [ ] Sin `networkx`, `graphlib` ni librerías de grafos/pathfinding.
- [ ] Coste de movimiento por zona destino (normal/priority=1, restricted=2, blocked=intransitable).
- [ ] Tránsito a restricted: reserva de capacidad de llegada antes de autorizar la salida.
- [ ] Capacidad por defecto=1; `max_drones` en start/end ignorado sin error.
- [ ] Conexiones bidireccionales; `a-b`/`b-a` tratadas como duplicado.
- [ ] Salidas liberan capacidad de origen antes de evaluar entradas (mismo turno).
- [ ] Plan de turno atómico; corrección independiente del orden de iteración de drones.
- [ ] stdout exacto: solo líneas de movimiento, visualización/métricas nunca lo contaminan.
- [ ] Errores de parseo con línea física (1-based) y causa clara.
- [ ] Sin variables globales mutables (estado en instancias o parámetros/retorno).

## Pruebas y evidencia real

<!-- Pega salida real de terminal, nunca descrita de memoria. -->

```text
$ pytest ...

$ make lint

$ make test
```

- [ ] Test nuevo visto en rojo antes de implementar (o se justifica por qué no aplica).
- [ ] Test en verde tras implementar.
- [ ] `make lint` (flake8 + mypy) en verde.
- [ ] `make test` en verde.

## Riesgos y reversión

<!-- Qué queda sabido-pendiente para un slice posterior. Cómo revertir si algo sale mal. -->

## Documentación y enseñanza

- [ ] `docs/PROGRESS.md` refleja el estado real (milestone, último slice, siguiente paso).
- [ ] `docs/SPEC_NOTES.md` actualizado si se resolvió/registró una zona gris del subject.
- [ ] `docs/EVALUATION.md` actualizado si este slice evidencia un ítem de rúbrica.
- [ ] Explicación lista para la defensa: problema, clases, invariante protegido, complejidad, ejemplo, prueba.

## Revisión de simplicidad

<!-- Qué se consideró y se descartó (abstracción, validación, config) y por qué la
     solución mínima sigue siendo correcta. -->

## Checklist de entrega

- [ ] Diff revisado: sin secretos, sin cambios accidentales en `maps/` (adjuntos oficiales, nunca se editan).
- [ ] CI en verde (`lint`, `test`), salvo RED intencional documentado arriba.
- [ ] PR enlazada al issue correspondiente y visible en el Project.
- [ ] Sin merge automático: Jose hace el merge manual a `main`.
