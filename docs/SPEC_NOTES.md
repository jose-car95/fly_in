# Fly-In 1.6 — zonas grises del subject (red de seguridad para la defensa)

Única fuente de verdad: el enunciado **v1.6** y la hoja de corrección de Intra.
Este documento fija cómo interpretamos lo que el subject deja ambiguo. Etiquetas:
**FACT** (lo dice el subject), **INTERPRETACIÓN** (lectura razonada de un hueco),
**DECISIÓN** (elección de ingeniería que hay que poder justificar en la defensa).
Toda ambigüedad nueva se registra aquí o en `PROGRESS.md` antes de implementarla.

## 1. Tránsito por zonas restricted (2 turnos)

- FACT: entrar en una zona `restricted` cuesta 2 turnos; el dron ocupa la conexión
  durante el tránsito.
- FACT: el dron DEBE llegar al destino al turno siguiente; no puede esperar en la
  conexión a que se libere sitio.
- INTERPRETACIÓN: por tanto, la salida hacia una restricted solo es legal si en el
  momento de salir se puede **reservar** capacidad del destino para el turno de llegada.
  El planificador reserva a futuro; el simulador lo verifica.
- FACT (salida): turno 1 imprime `D<ID>-<conexión>` (en vuelo); turno 2 imprime
  `D<ID>-<zona>` (llegada).
- ABIERTO: nombre textual exacto del token de conexión. Propuesta por defecto:
  `<origen>-<destino>`. Verificar contra lo que espera el evaluador antes de M3.
- ABIERTO: ventana exacta en que el tránsito consume capacidad del enlace (¿solo el
  turno de salida o ambos turnos?). Fijar con tests en M3/M4 antes de optimizar.

## 2. Orden de evaluación del turno atómico

- FACT: los drones que salen de una zona liberan su capacidad **ese mismo turno**; una
  zona debe tener hueco tras contar las salidas para aceptar entradas.
- DECISIÓN: el turno se calcula como plan completo y se aplica atómicamente
  (`SimulationState -> TurnPlan -> SimulationState`). Orden conceptual:
  1. Llegadas de tránsito que vencen este turno.
  2. Salidas candidatas de drones en zona.
  3. Reservas de enlaces y de llegadas restricted futuras.
  4. Las salidas liberan capacidad de origen.
  5. Validar entradas contra capacidad post-salidas.
  6. Validar uso total (no dirigido) de cada enlace contra su capacidad.
  7. Aplicar todo y emitir movimientos.
- DECISIÓN: la corrección nunca depende del orden de iteración de los drones. Nada de
  "muevo un dron y muto el estado" secuencial.
- INTERPRETACIÓN: los intercambios simultáneos por un mismo arco son legales solo si la
  capacidad del enlace admite ambas travesías y las zonas quedan válidas tras el turno.

## 3. "Priority debe preferirse en pathfinding" → algoritmo

- FACT: `priority` cuesta 1 turno pero "should be preferred in pathfinding".
- INTERPRETACIÓN: es una preferencia de desempate, no permiso para elegir un plan
  globalmente peor. Nunca sacrificamos makespan por pasar por priority.
- DECISIÓN concreta: en la búsqueda de caminos, ante coste igual, se prefiere el camino
  con más zonas priority (p. ej. coste efectivo `(turnos, -n_priority)` como clave
  lexicográfica, o un epsilon de desempate que no altere el orden por turnos).
  El desempate final debe ser determinista (p. ej. orden alfabético de zona) para que
  los tests sean estables.

## 4. Capacidades de zona y de conexión

- FACT: capacidad por defecto de zona y de conexión = 1; valores explícitos deben ser
  enteros positivos.
- FACT: `max_drones` en `start_hub` y `end_hub` se **ignora** y no es error de
  validación: los terminales tienen capacidad ilimitada.
- FACT: las conexiones son bidireccionales; `a-b` y `b-a` son la misma conexión y su
  repetición es un duplicado (error).
- INTERPRETACIÓN: `max_link_capacity` es compartida por las travesías simultáneas en
  ambos sentidos (no una capacidad por sentido).
- DECISIÓN: identidad canónica no ordenada para la igualdad de conexiones; travesía
  dirigida para movimiento y salida.
- DECISIÓN: distinguir capacidad efectiva (∞ en terminales) de la declarada ignorada,
  por si la visualización o `--capacity-info` quieren mostrarla.
- Invariantes por turno aplicado:
  `ocupación_zona_regular ≤ max_drones_efectivo` y `uso_enlace ≤ max_link_capacity`.

## 5. Parser: huecos menores

- FACT: comentarios con `#` se ignoran; el subject dice que `nb_drones` va en la
  "primera línea".
- INTERPRETACIÓN: los mapas oficiales anteponen comentarios de título, así que
  `nb_drones` debe ser la primera línea **significativa** (no vacía, no comentario).
  Los errores conservan el número de línea físico (1-based).
- FACT: nombres de zona sin guiones ni espacios; tipos válidos solo
  `normal|blocked|restricted|priority`; conexiones solo entre zonas ya definidas;
  exactamente un start y un end; metadatos entre corchetes con orden libre.
- INTERPRETACIÓN: claves de metadatos desconocidas se rechazan (un typo cambiaría
  capacidades o rutas en silencio). Claves repetidas en un bloque → error.
- DECISIÓN: self-loops (`a-a`) no están especificados → rechazar con error claro.
- FACT: cualquier error de parseo detiene el programa con mensaje claro de línea y causa.

## 6. Grafo y salida

- FACT: grafo propio, sin networkx/graphlib ni similares; coste según la zona destino
  (normal/priority 1, restricted 2, blocked intransitable).
- DECISIÓN: las zonas blocked existen parseadas (para visualizar) pero no en la
  adyacencia transitable. Si start no alcanza end → error claro de mapa no resoluble,
  nunca simulación infinita.
- FACT (salida): una línea por turno, tokens separados por espacio, drones parados
  omitidos, entregados fuera del tracking, fin al entregar todos.
- DECISIÓN: orden estable de tokens por ID de dron ascendente.
- FACT: el stdout obligatorio contiene solo líneas de movimiento; visualización y
  métricas van por flag aparte o stderr.

## 7. Validez vs calidad

La validez de un schedule es binaria y la comprueba un **validador independiente** del
planificador. Las métricas de calidad (turnos totales como primaria; drones movidos por
turno, media por dron, coste ponderado como secundarias) se miden aparte. Un plan
inválido rápido siempre pierde frente a uno válido lento.
