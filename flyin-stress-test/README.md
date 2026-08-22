# Fly-In · test de estrés de horarios

Un solo fichero de Python (solo librería estándar) y una carpeta de 960
mapas. Ejecuta **cualquier** proyecto Fly-In sobre esos mapas y comprueba
cada horario con un validador **independiente** que reconstruye las reglas
leyendo el propio mapa. Cuando un horario es ilegal, dice **por qué**.

No escribe nada dentro del proyecto que evalúa: ni informes, ni carpetas de
fallos, ni `__pycache__`. Todo sale por pantalla, en español.

## Cómo se ejecuta

Copia `stress_test.py` y la carpeta `mapas/` **dentro de la carpeta donde
está el punto de entrada del proyecto** (junto a su `__main__.py` o su
`main.py`) y lanza:

```bash
python3 stress_test.py
```

Ya está. No hay que buscar rutas ni configurar nada: el script mira qué hay
a su lado y decide cómo arrancar el solver.

Si la detección automática no acierta (proyecto raro, script con otro
nombre), se le dice el comando a mano; `{map}` se sustituye por la ruta de
cada mapa:

```bash
python3 stress_test.py --cmd "./fly_in {map}"
python3 stress_test.py --cmd "python3 -m mi_paquete {map}"
```

Termina con código de salida `0` si todo es legal y `1` si hay algún
horario ilegal, así que sirve tal cual en un script o en CI.

## Cómo encuentra la forma de ejecutar el proyecto

Primero decide **qué** lanzar, mirando la carpeta en la que está:

1. `__init__.py` + `__main__.py` → es un paquete: `python -m <paquete>`,
   con `PYTHONPATH` apuntando a la carpeta de arriba (no hace falta
   instalar nada).
2. Solo `__main__.py` → carpeta ejecutable: `python <carpeta>`.
3. `main.py`, `fly_in.py`, `flyin.py` o `solver.py` → `python <script>`.
4. Un ejecutable `fly_in` o `flyin` → se lanza tal cual.

Después decide **con qué** lanzarlo, probando por orden y quedándose con el
primero que funcione de verdad sobre un mapa real:

1. el intérprete con el que arrancaste el test (`python3 stress_test.py`,
   `.venv/bin/python stress_test.py`, `uv run python stress_test.py`…);
2. cualquier entorno virtual del proyecto (`.venv/`, `venv/`, `env/`, en
   esa carpeta o hasta cuatro niveles por encima);
3. `uv run --frozen` si el proyecto tiene `pyproject.toml` **y** `uv.lock`,
   con el entorno redirigido a una carpeta temporal (`UV_PROJECT_ENVIRONMENT`)
   para no crear un `.venv` dentro del proyecto;
4. como último recurso, un entorno virtual **de usar y tirar** en la carpeta
   temporal del sistema, con las dependencias declaradas en
   `requirements.txt` o en `[project].dependencies` instaladas dentro.

Lo temporal se borra al terminar. Cada intento se ve en pantalla con su
resultado, así que si falla se sabe exactamente por qué (típicamente un
`ModuleNotFoundError`).

## Qué mide

Cada mapa se ejecuta en un subproceso (varios a la vez, uno por núcleo) y
su salida se **reproduce turno a turno** contra el mapa. El validador
comprueba:

- que cada dron se mueve como mucho una vez por turno;
- que ninguna **conexión** se cruza más veces que su `max_link_capacity`
  (se cuenta por turno, sumando los dos sentidos, y se reserva al despegar);
- que un dron en vuelo hacia una zona `restricted` **aterriza
  obligatoriamente** al turno siguiente: sobre una conexión no se espera;
- que ninguna **zona** tiene más drones parados que su `max_drones`
  (`start_hub` y `end_hub` son ilimitados);
- que solo se entra en `restricted` en dos turnos y nunca en `blocked`;
- que al final **todos** los drones están en el `end_hub` y ninguno se
  quedó en vuelo.

Además cuenta como fallo que el solver aborte con código distinto de 0 o
que no termine dentro del timeout.

Formato de salida que se asume (el del subject): una línea por turno,
tokens separados por espacios, `D<id>-<zona>` al llegar a una zona y
`D<id>-<a>-<b>` mientras se vuela hacia una `restricted`. El par en vuelo se
lee sin importar el orden. Si la salida no encaja con ese formato, saldrán
"fallos" que en realidad son de formato: eso se ve enseguida porque todos
caen en la causa `token_invalido`.

## Qué imprime

1. **Resultado por mapa**: una línea por mapa, `OK` o `KO`, y en los KO el
   motivo exacto (`turno 3: la zona 'z1' tiene 2 drones parados y su
   capacidad es 1`). Con `--only-failures` se listan solo los KO.
2. **Resumen**: total, OK, KO, tiempo y desglose por categoría.
3. **Por qué falla**: los KO agrupados por causa, con una explicación de qué
   error de diseño produce esa causa y, por cada una, un ejemplo completo:
   el mapa entero y la salida que dio el solver, para poder reproducirlo a
   mano.
4. **Veredicto**: `PASS` o `FAIL`.

Como no se guarda nada en disco, para conservar un informe basta redirigir:
`python3 stress_test.py > informe.txt`.

## Los mapas

960 mapas sintéticos en dos familias:

- `mapas/lineales/` (672) — una única ruta `start → … → goal`.
- `mapas/no_lineales/` (288) — varias ramas en paralelo que se juntan en una
  zona común antes del `goal`.

No son aleatorios: todos tienen la forma que puede romper a un planificador
"optimista" — una zona `restricted` con capacidad ≥ 2, una conexión que deja
pasar más de un dron por turno, y algo **más estrecho aguas abajo** donde
atascarse. Varían la longitud de la cadena, el tipo y la capacidad de cada
zona, la capacidad de las conexiones y el tamaño de la flota.

El fallo que buscan: entrar en una zona `restricted` cuesta 2 turnos (uno en
vuelo, otro aterrizando) y en la conexión no se puede esperar. Si el
planificador deja despegar a otro dron hacia esa zona el mismo turno en que
uno sale, sin **reservar** la plaza de llegada, y aguas abajo hay un cuello
de botella que no drena a ese ritmo, la zona termina con más drones de los
que caben. El programa imprime su salida sin dar error, pero el horario es
ilegal. Con los mapas oficiales no aparece: van holgados.

## Opciones

```
--cmd "<comando> {map}"   comando del solver, si la detección no acierta
--maps-dir DIR            otra carpeta de mapas (recorre subcarpetas)
--jobs N                  mapas en paralelo (por defecto: uno por núcleo)
--timeout SEG             límite por mapa (por defecto: 10)
--only-failures           listar solo los KO
--examples N              ejemplos completos por causa (por defecto: 1)
--version
```

`--maps-dir` sirve para pasarle los mapas oficiales del proyecto o los
tuyos: el validador es el mismo.
