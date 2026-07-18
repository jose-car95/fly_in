# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: M0 (no empezado).
- Último slice completado: ninguno.
- Verificado con comandos: nada todavía.
- Siguiente paso propuesto: ejecutar `/bootstrap-github` y después el primer slice de M0.

## Decisiones tomadas

| Fecha | Decisión | Motivo |
| --- | --- | --- |
| — | `nb_drones` = primera línea significativa (no física) | Los mapas oficiales anteponen comentarios |
| — | Claves de metadatos desconocidas → error | Un typo cambiaría rutas en silencio |
| — | Self-loops rechazados | No especificados por el subject |
| — | Salida ordenada por ID de dron ascendente | Determinismo y tests estables |
| — | Priority = desempate lexicográfico a coste igual | Ver SPEC_NOTES §3 |

## Preguntas abiertas

- Token textual exacto de la conexión en vuelo (`<origen>-<destino>`?). Fijar antes de M3.
- Ventana exacta de consumo de capacidad del enlace durante el tránsito restricted
  (¿un turno o los dos?). Fijar con tests en M3/M4.

## GitHub: qué se mueve solo y qué muevo a mano

(Se rellena al ejecutar `/bootstrap-github`.)

- Automatizaciones del Project activas: —
- Automatizaciones que requieren clics en la web: —
- Movimientos manuales que me tocan a mí: —

## Registro de sesiones (una línea por sesión)

| Fecha | Qué se hizo | Estado al cerrar |
| --- | --- | --- |
| — | — | — |
