#!/usr/bin/env python3
"""Fly-In schedule stress test - portable, standalone, stdlib only.

Drop this file next to a `mapas/` folder inside ANY Fly-In project (beside
its `__main__.py` or `main.py`) and run it. It works out by itself how to
launch that solver - which interpreter, which virtualenv, which
dependencies - runs it over every map and judges the printed schedule with
an independent replay that re-derives every rule from the map itself. On
every illegal map it says exactly WHY.

Design constraints, on purpose:

  * standard library only, one file, no install;
  * it writes NOTHING inside the project under test - no report files, no
    `failures/` folder, no `__pycache__` (bytecode writing is disabled for
    the solver too). A throwaway virtualenv, if one is ever needed, is
    built in the system temp folder and deleted on exit;
  * everything it has to say goes to the screen, in Spanish.

Output-format assumption (from the Fly-In subject): one line per turn,
tokens separated by spaces, a token is either `D<id>-<zone>` (a drone
arrives at or steps into a zone) or `D<id>-<a>-<b>` (a drone in flight on a
connection, the first of the two turns a restricted zone costs). The
in-flight pair is read order-agnostically, so a solver that prints
`dest-origin` is accepted too.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import math
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from dataclasses import dataclass
from pathlib import Path

__version__ = "2.0"

NORMAL = "normal"
RESTRICTED = "restricted"
PRIORITY = "priority"

# Turns it costs to ENTER a zone of each type. A restricted zone costs two
# (in-flight turn, then landing); a blocked zone can never be entered.
MOVE_COST = {NORMAL: 1, PRIORITY: 1, RESTRICTED: 2}


# --------------------------------------------------------------------------
# Map model.
# --------------------------------------------------------------------------


@dataclass
class Zone:
    """A landing zone: its name, type and how many drones it holds."""

    name: str
    kind: str
    capacity: float  # math.inf on start/end: their declared limit is ignored


@dataclass
class Map:
    """A parsed Fly-In map: enough to replay and judge a schedule."""

    nb_drones: int
    zones: dict[str, Zone]
    links: dict[frozenset[str], int]  # undirected connection -> capacity
    start: str
    end: str
    text: str


class InvalidSchedule(Exception):
    """An illegal schedule, tagged with the kind of illegality.

    Attributes:
        code: short machine tag used to group failures and to pick the
            explanation shown in the report.
        message: the human sentence, in Spanish, shown next to the map.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MapParseError(Exception):
    """Raised when a map file cannot be read into the model."""


class SetupError(Exception):
    """Raised when no way of launching the solver could be found."""


# --------------------------------------------------------------------------
# Map parser: reads a map file off disk into the model, so output can be
# judged for any map, including the project's own official ones.
# --------------------------------------------------------------------------


class Parser:
    """Turns Fly-In map text into a Map, reporting the offending line.

    The format (from the subject and the official maps):
        nb_drones: N
        start_hub: name x y [attrs]
        end_hub:   name x y [attrs]
        hub:       name x y [attrs]
        connection: a-b [attrs]
    Attributes inside [...] are space-separated `key=value` pairs; the ones
    that matter are `zone=` (normal|priority|restricted|blocked),
    `max_drones=` and `max_link_capacity=`. Lines are comment-stripped at
    `#` and blanks skipped. Zones are read before connections so endpoints
    resolve.
    """

    def __init__(self, text: str, source: str = "<mapa>") -> None:
        self._text = text
        self._source = source

    def parse(self) -> Map:
        """Parse the whole text; raise MapParseError on the first problem."""
        nb_drones: int | None = None
        zones: dict[str, Zone] = {}
        start: str | None = None
        end: str | None = None
        conn_bodies: list[tuple[int, str]] = []
        for lineno, raw in enumerate(self._text.splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            key, sep, rest = line.partition(":")
            if not sep:
                raise self._err(lineno, f"línea sin ':' -> {raw!r}")
            key, rest = key.strip(), rest.strip()
            if key == "nb_drones":
                nb_drones = self._int(lineno, rest, "nb_drones")
            elif key in ("start_hub", "end_hub", "hub"):
                zone = self._parse_zone(lineno, rest, key)
                zones[zone.name] = zone
                if key == "start_hub":
                    start = zone.name
                elif key == "end_hub":
                    end = zone.name
            elif key == "connection":
                conn_bodies.append((lineno, rest))
            else:
                raise self._err(lineno, f"tipo de línea desconocido {key!r}")
        links = self._parse_connections(conn_bodies, zones)
        if nb_drones is None:
            raise self._err(0, "falta la línea 'nb_drones:'")
        if start is None or end is None:
            raise self._err(0, "falta start_hub o end_hub")
        return Map(nb_drones, zones, links, start, end, self._text)

    def _parse_zone(self, lineno: int, rest: str, key: str) -> Zone:
        body, attrs = self._split_attrs(rest)
        parts = body.split()
        if len(parts) < 3:
            raise self._err(
                lineno, f"una zona necesita 'nombre x y' -> {rest!r}"
            )
        name = parts[0]
        if key in ("start_hub", "end_hub"):
            return Zone(name, NORMAL, math.inf)
        kind = attrs.get("zone", NORMAL)
        cap = self._int(lineno, attrs["max_drones"], "max_drones") \
            if "max_drones" in attrs else 1
        return Zone(name, kind, cap)

    def _parse_connections(
        self,
        bodies: list[tuple[int, str]],
        zones: dict[str, Zone]
    ) -> dict[frozenset[str], int]:
        links: dict[frozenset[str], int] = {}
        for lineno, rest in bodies:
            body, attrs = self._split_attrs(rest)
            a, b = self._split_endpoints(lineno, body.strip(), zones)
            cap = self._int(
                lineno, attrs["max_link_capacity"], "max_link_capacity"
            ) if "max_link_capacity" in attrs else 1
            links[frozenset((a, b))] = cap
        return links

    def _split_endpoints(
        self, lineno: int, body: str, zones: dict[str, Zone]
    ) -> tuple[str, str]:
        # Names normally hold no '-', but resolve against known zones so a
        # dashed name still parses: pick the split where both sides exist.
        parts = body.split("-")
        if len(parts) == 2 and parts[0] in zones and parts[1] in zones:
            return parts[0], parts[1]
        for i, char in enumerate(body):
            if char == "-":
                a, b = body[:i], body[i + 1:]
                if a in zones and b in zones:
                    return a, b
        raise self._err(
            lineno, f"los extremos de la conexión no son zonas: {body!r}"
        )

    @staticmethod
    def _split_attrs(rest: str) -> tuple[str, dict[str, str]]:
        if "[" not in rest:
            return rest.strip(), {}
        head, _, tail = rest.partition("[")
        inside = tail.rstrip().rstrip("]")
        attrs: dict[str, str] = {}
        for token in inside.split():
            k, _, v = token.partition("=")
            attrs[k] = v
        return head.strip(), attrs

    def _int(self, lineno: int, text: str, what: str) -> int:
        try:
            return int(text)
        except ValueError:
            raise self._err(lineno, f"{what} no es un entero: {text!r}")

    def _err(self, lineno: int, msg: str) -> MapParseError:
        where = f"{self._source}:{lineno}" if lineno else self._source
        return MapParseError(f"{where}: {msg}")


# --------------------------------------------------------------------------
# Independent validator: replays the solver's output against the map.
# --------------------------------------------------------------------------


class Validator:
    """Judges a schedule by replaying it, independent of any solver.

    It tracks every drone by id: where it stands and, if mid restricted
    transit, which zone it must land on next turn. After each turn it checks
    that no zone holds more parked drones than its capacity and that no link
    was crossed over its capacity; at the end every drone must sit on the
    end hub with none left in flight.
    """

    def __init__(self, game_map: Map, lines: list[str]) -> None:
        self._map = game_map
        self._lines = lines
        self._pos: dict[int, str] = {}
        self._flying: dict[int, str | None] = {}

    def validate(self) -> None:
        """Replay the whole schedule; raise on the first illegal thing."""
        ids = range(1, self._map.nb_drones + 1)
        self._pos = {i: self._map.start for i in ids}
        self._flying = {i: None for i in ids}
        for turn, line in enumerate(self._lines, start=1):
            self._play_turn(line, turn)
            self._check_occupancy(turn)
        self._check_all_delivered()

    def _play_turn(self, line: str, turn: int) -> None:
        pending = {i for i, dest in self._flying.items() if dest}
        moved: set[int] = set()
        crossings: dict[frozenset[str], int] = {}
        for token in line.split():
            drone_id, link = self._apply_token(token, turn)
            if drone_id in moved:
                raise InvalidSchedule(
                    "doble_movimiento",
                    f"turno {turn}: el dron {drone_id} se mueve dos veces"
                )
            moved.add(drone_id)
            if link is not None:
                crossings[link] = crossings.get(link, 0) + 1
        for link, count in crossings.items():
            cap = self._map.links[link]
            if count > cap:
                a, b = sorted(link)
                raise InvalidSchedule(
                    "enlace_saturado",
                    f"turno {turn}: la conexión {a}-{b} se cruza {count} "
                    f"veces y su capacidad es {cap}"
                )
        stranded = pending - moved
        if stranded:
            raise InvalidSchedule(
                "vuelo_sin_aterrizar",
                f"turno {turn}: el dron {min(stranded)} estaba en vuelo y "
                f"no aterriza (no se puede esperar sobre una conexión)"
            )

    def _apply_token(
        self, token: str, turn: int
    ) -> tuple[int, frozenset[str] | None]:
        drone_id, body = self._parse_prefix(token, turn)
        parts = body.split("-")
        if len(parts) == 1:
            return drone_id, self._apply_arrival(drone_id, parts[0], turn)
        if len(parts) == 2:
            return drone_id, self._apply_flight(
                drone_id, parts[0], parts[1], turn
            )
        raise InvalidSchedule(
            "token_invalido", f"turno {turn}: token mal formado {token!r}"
        )

    def _parse_prefix(self, token: str, turn: int) -> tuple[int, str]:
        prefix, sep, body = token.partition("-")
        digits = prefix[1:]
        if not sep or not body or prefix[:1] != "D" or not digits.isdigit():
            raise InvalidSchedule(
                "token_invalido", f"turno {turn}: token mal formado {token!r}"
            )
        drone_id = int(digits)
        if drone_id not in self._pos:
            raise InvalidSchedule(
                "token_invalido",
                f"turno {turn}: el token nombra al dron {drone_id}, que no "
                f"existe (nb_drones = {self._map.nb_drones})"
            )
        return drone_id, body

    def _apply_flight(
        self, drone_id: int, a: str, b: str, turn: int
    ) -> frozenset[str]:
        if self._flying[drone_id] is not None:
            raise InvalidSchedule(
                "despegue_en_vuelo",
                f"turno {turn}: el dron {drone_id} despega cuando todavía "
                f"está en vuelo"
            )
        here = self._pos[drone_id]
        # Read the in-flight pair order-agnostically: the origin is
        # whichever endpoint the drone currently stands on.
        if here == a:
            target = b
        elif here == b:
            target = a
        else:
            raise InvalidSchedule(
                "posicion_incoherente",
                f"turno {turn}: el dron {drone_id} vuela por {a}-{b} pero "
                f"está en {here!r}"
            )
        if frozenset((here, target)) not in self._map.links:
            raise InvalidSchedule(
                "sin_conexion",
                f"turno {turn}: no existe la conexión {here}-{target}"
            )
        if self._map.zones[target].kind != RESTRICTED:
            raise InvalidSchedule(
                "vuelo_hacia_no_restricted",
                f"turno {turn}: token de vuelo hacia {target!r}, que no es "
                f"una zona restricted (solo esas cuestan dos turnos)"
            )
        self._flying[drone_id] = target
        return frozenset((here, target))

    def _apply_arrival(
        self, drone_id: int, zone: str, turn: int
    ) -> frozenset[str] | None:
        if zone not in self._map.zones:
            raise InvalidSchedule(
                "token_invalido", f"turno {turn}: zona desconocida {zone!r}"
            )
        pending = self._flying[drone_id]
        if pending is not None:
            if zone != pending:
                raise InvalidSchedule(
                    "aterrizaje_erroneo",
                    f"turno {turn}: el dron {drone_id} debía aterrizar en "
                    f"{pending!r} y aparece en {zone!r}"
                )
            self._flying[drone_id] = None
            self._pos[drone_id] = zone
            return None  # the link was already metered on take-off
        here = self._pos[drone_id]
        if frozenset((here, zone)) not in self._map.links:
            raise InvalidSchedule(
                "sin_conexion",
                f"turno {turn}: no existe la conexión {here}-{zone}"
            )
        if MOVE_COST.get(self._map.zones[zone].kind) != 1:
            raise InvalidSchedule(
                "entrada_en_un_turno",
                f"turno {turn}: no se puede entrar en la zona {zone!r} con "
                f"un solo turno (restricted cuesta 2, blocked es "
                f"intransitable)"
            )
        self._pos[drone_id] = zone
        return frozenset((here, zone))

    def _check_occupancy(self, turn: int) -> None:
        counts: dict[str, int] = {}
        for drone_id, zone in self._pos.items():
            if self._flying[drone_id] is None:
                counts[zone] = counts.get(zone, 0) + 1
        for zone, count in counts.items():
            cap = self._map.zones[zone].capacity
            if count > cap:
                raise InvalidSchedule(
                    "zona_llena",
                    f"turno {turn}: la zona {zone!r} tiene {count} drones "
                    f"parados y su capacidad es {cap:g}"
                )

    def _check_all_delivered(self) -> None:
        for drone_id, zone in self._pos.items():
            if self._flying[drone_id] is not None:
                raise InvalidSchedule(
                    "sin_entregar",
                    f"el dron {drone_id} se queda en vuelo hacia "
                    f"{self._flying[drone_id]!r} y nunca aterriza"
                )
            if zone != self._map.end:
                raise InvalidSchedule(
                    "sin_entregar",
                    f"el dron {drone_id} termina en {zone!r} y no en el "
                    f"end_hub {self._map.end!r}"
                )


# --------------------------------------------------------------------------
# Launching the solver: work out interpreter, entry point and dependencies
# without leaving anything behind in the project under test.
# --------------------------------------------------------------------------


@dataclass
class Solver:
    """A ready-to-run solver command."""

    label: str
    template: str  # holds `{map}`, replaced by each map path
    cwd: Path | None = None
    extra_env: dict[str, str] | None = None

    def command(self, map_path: Path) -> list[str]:
        """Build the argv for one map."""
        quoted = shlex.quote(str(map_path))
        if "{map}" in self.template:
            return shlex.split(self.template.replace("{map}", quoted))
        return shlex.split(f"{self.template} {quoted}")

    def environment(self) -> dict[str, str]:
        """The solver's environment, with bytecode writing switched off.

        Writing `__pycache__` folders inside the project under test would
        be a trace left behind, so the child process is told not to.
        """
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if self.extra_env:
            env.update(self.extra_env)
        return env

    def run(self, map_path: Path, timeout: float) -> str:
        """Run the solver on one map and return its stdout.

        Raises:
            InvalidSchedule: if it times out or exits non-zero. Both are
                solver failures, reported like any other illegal result.
        """
        try:
            proc = subprocess.run(
                self.command(map_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.cwd) if self.cwd else None,
                env=self.environment()
            )
        except subprocess.TimeoutExpired:
            raise InvalidSchedule(
                "timeout",
                f"el solver no terminó en {timeout:g}s (posible bucle "
                f"infinito o búsqueda que no converge)"
            )
        if proc.returncode != 0:
            tail = _last_line(proc.stderr)
            raise InvalidSchedule(
                "solver_error",
                f"el solver terminó con código {proc.returncode}: {tail}"
            )
        return proc.stdout


@dataclass
class Entrypoint:
    """How to invoke a solver once an interpreter has been chosen.

    Attributes:
        label: human description, shown on screen.
        args: arguments that go after the interpreter (e.g. -m flyin).
        cwd: working directory the solver is run from.
        extra_env: environment additions, e.g. PYTHONPATH for the import
            root, so the package is importable without installing it.
        interpreted: False for a standalone executable, which is run as is.
    """

    label: str
    args: list[str]
    cwd: Path
    extra_env: dict[str, str]
    interpreted: bool = True


def _last_line(text: str) -> str:
    """The last non-empty line of a stream, trimmed for one-line reports."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "(sin mensaje)"
    tail = lines[-1]
    return tail if len(tail) <= 140 else tail[:137] + "..."


def _venv_python(folder: Path) -> Path | None:
    """The interpreter inside a virtualenv folder, if there is one."""
    for rel in ("bin/python3", "bin/python", "Scripts/python.exe"):
        candidate = folder / rel
        if candidate.exists():
            return candidate
    return None


class SolverLocator:
    """Works out how to launch the solver that surrounds this script.

    The ladder, cheapest first: the interpreter this script was launched
    with, then any virtualenv sitting in the project, then uv if the
    project is uv-managed, and only as a last resort a throwaway virtualenv
    built in the system temp folder with the project's declared
    dependencies installed into it. Each rung is tried on one real map, so
    the one that gets picked is the one that provably works.
    """

    VENV_DIRS = (".venv", "venv", "env")
    SCRIPTS = ("main.py", "fly_in.py", "flyin.py", "solver.py")
    EXECUTABLES = ("fly_in", "flyin")

    def __init__(self, here: Path, probe_map: Path, timeout: float) -> None:
        self._here = here
        self._probe_map = probe_map
        self._timeout = timeout
        self._temp_dirs: list[Path] = []
        self._notes: list[str] = []

    def cleanup(self) -> None:
        """Delete anything temporary that was built while locating."""
        for folder in self._temp_dirs:
            shutil.rmtree(folder, ignore_errors=True)
        self._temp_dirs.clear()

    def locate(self) -> Solver:
        """Return the first solver command that runs a map successfully.

        Raises:
            SetupError: when no rung of the ladder produced a working
                command; the message lists what was tried and why each
                attempt failed.
        """
        entry = self._entrypoint()
        print(f"  · punto de entrada: {entry.label}")
        for solver in self._direct_candidates(entry):
            if self._probe(solver):
                return solver
        # Nothing already on the machine could run it, which normally means
        # the dependencies are missing. Build an environment elsewhere, one
        # rung at a time so the cheap one is never paid for twice.
        for build in (self._uv_candidate, self._temp_venv_candidate):
            prepared = build(entry)
            if prepared is not None and self._probe(prepared):
                return prepared
        raise SetupError(
            "no he conseguido ejecutar el solver. Intentos:\n"
            + "\n".join(f"    - {note}" for note in self._notes)
            + "\n  Usa --cmd \"<tu comando> {map}\" para decírmelo a mano."
        )

    # ---- entry point -----------------------------------------------------

    def _entrypoint(self) -> Entrypoint:
        """Decide what to run: a package, a folder, a script or a binary."""
        package = self._package()
        if package is not None:
            dotted, root = package
            return Entrypoint(
                label=f"paquete '{dotted}' (python -m {dotted})",
                args=["-m", dotted],
                cwd=root,
                extra_env={"PYTHONPATH": self._pythonpath(root)}
            )
        if (self._here / "__main__.py").exists():
            return Entrypoint(
                label=f"carpeta ejecutable '{self._here.name}' "
                      f"(python {self._here.name})",
                args=[str(self._here)],
                cwd=self._here.parent,
                extra_env={"PYTHONPATH": self._pythonpath(self._here.parent)}
            )
        for name in self.SCRIPTS:
            script = self._here / name
            if script.exists():
                return Entrypoint(
                    label=f"script '{name}' (python {name})",
                    args=[str(script)],
                    cwd=self._here,
                    extra_env={"PYTHONPATH": self._pythonpath(self._here)}
                )
        for name in self.EXECUTABLES:
            binary = self._here / name
            if binary.exists() and os.access(binary, os.X_OK):
                return Entrypoint(
                    label=f"ejecutable './{name}'",
                    args=[str(binary)],
                    cwd=self._here,
                    extra_env={},
                    interpreted=False
                )
        raise SetupError(
            f"no encuentro por dónde se lanza el solver en {self._here}/. "
            f"Esperaba un __main__.py, un main.py o un ejecutable "
            f"fly_in/flyin al lado de este script.\n"
            f"  Copia stress_test.py y mapas/ junto al punto de entrada, o "
            f"usa --cmd \"<tu comando> {{map}}\"."
        )

    def _package(self) -> tuple[str, Path] | None:
        """The dotted package name and import root, if we sit in one."""
        if not (self._here / "__main__.py").exists():
            return None
        if not (self._here / "__init__.py").exists():
            return None
        parts = [self._here.name]
        root = self._here.parent
        while (root / "__init__.py").exists():
            parts.append(root.name)
            root = root.parent
        return ".".join(reversed(parts)), root

    @staticmethod
    def _pythonpath(root: Path) -> str:
        """PYTHONPATH with the import root first, keeping any existing one."""
        current = os.environ.get("PYTHONPATH", "")
        return str(root) + (os.pathsep + current if current else "")

    # ---- candidates ------------------------------------------------------

    def _direct_candidates(self, entry: Entrypoint) -> list[Solver]:
        """Commands that need nothing installed or created first."""
        if not entry.interpreted:
            return [Solver(
                label=entry.args[0],
                template=f"{shlex.quote(entry.args[0])} {{map}}",
                cwd=entry.cwd,
                extra_env=entry.extra_env
            )]
        return [
            self._with_interpreter(entry, python)
            for python in self._interpreters()
        ]

    def _with_interpreter(self, entry: Entrypoint, python: Path) -> Solver:
        args = " ".join(shlex.quote(a) for a in entry.args)
        return Solver(
            label=f"{python} {args}",
            template=f"{shlex.quote(str(python))} {args} {{map}}",
            cwd=entry.cwd,
            extra_env=entry.extra_env
        )

    def _interpreters(self) -> list[Path]:
        """Interpreters worth trying, most likely first, deduplicated."""
        found: list[Path] = [Path(sys.executable)]
        bases = [self._here, *list(self._here.parents)[:4]]
        for base in bases:
            for name in self.VENV_DIRS:
                python = _venv_python(base / name)
                if python is not None:
                    found.append(python)
        unique: list[Path] = []
        seen: set[str] = set()
        for python in found:
            # Deduplicate by path, NOT by resolved target: a virtualenv's
            # python is a symlink to the base interpreter, and resolving it
            # would collapse the two even though only one of them sees the
            # virtualenv's installed packages.
            key = str(python.absolute())
            if key not in seen:
                seen.add(key)
                unique.append(python)
        return unique

    def _uv_candidate(self, entry: Entrypoint) -> Solver | None:
        """`uv run` for a locked uv project, with its venv sent to temp."""
        if not entry.interpreted:
            return None
        uv = shutil.which("uv")
        root = self._project_root()
        if uv is None or root is None:
            return None
        if not (root / "uv.lock").exists():
            return None  # without a lock, uv would write one: that is a trace
        temp = Path(tempfile.mkdtemp(prefix="flyin-stress-uv-"))
        self._temp_dirs.append(temp)
        env = dict(entry.extra_env)
        env["UV_PROJECT_ENVIRONMENT"] = str(temp / "venv")
        args = " ".join(shlex.quote(a) for a in entry.args)
        print("  · preparando entorno con uv (fuera del proyecto)...")
        return Solver(
            label=f"uv run --frozen --project {root} python {args}",
            template=(
                f"{shlex.quote(uv)} run --frozen --project "
                f"{shlex.quote(str(root))} python {args} {{map}}"
            ),
            cwd=entry.cwd,
            extra_env=env
        )

    def _temp_venv_candidate(self, entry: Entrypoint) -> Solver | None:
        """A throwaway virtualenv in temp with the declared deps in it."""
        if not entry.interpreted:
            return None
        install = self._dependency_install_args()
        if install is None:
            return None
        pip_args, description = install
        temp = Path(tempfile.mkdtemp(prefix="flyin-stress-venv-"))
        self._temp_dirs.append(temp)
        print(f"  · creando entorno virtual temporal en {temp} e instalando "
              f"{description}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(temp / "venv")],
                capture_output=True,
                text=True,
                check=True
            )
            python = _venv_python(temp / "venv")
            if python is None:
                raise SetupError("el entorno virtual no trae intérprete")
            subprocess.run(
                [str(python), "-m", "pip", "install", "--quiet", *pip_args],
                capture_output=True,
                text=True,
                check=True,
                timeout=600
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                SetupError) as err:
            detail = getattr(err, "stderr", "") or str(err)
            self._notes.append(
                f"entorno virtual temporal: no se pudo preparar "
                f"({_last_line(str(detail))})"
            )
            return None
        return self._with_interpreter(entry, python)

    def _project_root(self) -> Path | None:
        """The nearest folder above us holding project metadata."""
        for base in [self._here, *list(self._here.parents)[:4]]:
            for marker in ("pyproject.toml", "requirements.txt", "setup.py"):
                if (base / marker).exists():
                    return base
        return None

    def _dependency_install_args(self) -> tuple[list[str], str] | None:
        """pip arguments for the project's declared runtime dependencies."""
        root = self._project_root()
        if root is None:
            return None
        requirements = root / "requirements.txt"
        if requirements.exists():
            return ["-r", str(requirements)], requirements.name
        deps = self._pyproject_dependencies(root / "pyproject.toml")
        if deps:
            return list(deps), ", ".join(deps)
        return None

    @staticmethod
    def _pyproject_dependencies(pyproject: Path) -> list[str]:
        """[project].dependencies, or nothing when they cannot be read."""
        if not pyproject.exists():
            return []
        try:
            import tomllib
        except ImportError:  # Python 3.10 ships no TOML reader
            return []
        try:
            data = tomllib.loads(pyproject.read_text())
        except (tomllib.TOMLDecodeError, OSError):
            return []
        project = data.get("project", {})
        deps = project.get("dependencies", [])
        return [str(dep) for dep in deps if isinstance(dep, str)]

    # ---- probing ---------------------------------------------------------

    def _probe(self, solver: Solver) -> bool:
        """Try a candidate on one real map; say whether it produced output."""
        print(f"  · probando: {solver.label} ... ", end="", flush=True)
        try:
            output = solver.run(self._probe_map, max(self._timeout, 20.0))
        except InvalidSchedule as err:
            print(f"KO ({err.message})", flush=True)
            self._notes.append(f"{solver.label}: {err.message}")
            return False
        except (OSError, ValueError) as err:
            print(f"KO ({err})", flush=True)
            self._notes.append(f"{solver.label}: {err}")
            return False
        if not output.strip():
            print("KO (no imprime nada)", flush=True)
            self._notes.append(f"{solver.label}: no imprime nada")
            return False
        print("OK", flush=True)
        return True


# --------------------------------------------------------------------------
# Running the battery.
# --------------------------------------------------------------------------


@dataclass
class CaseResult:
    """What happened on one map."""

    path: Path
    category: str
    ok: bool
    code: str = ""
    reason: str = ""
    output: str = ""


class Progress:
    """Thread-safe progress line: how far along, how fast, how much left."""

    def __init__(self, total: int) -> None:
        self._total = total
        self._done = 0
        self._failing = 0
        self._started = time.monotonic()
        self._lock = threading.Lock()
        # About ten updates over the run, never noisier than every 50 maps.
        self._step = max(50, total // 10)

    def tick(self, failed: bool) -> None:
        """Count one finished map and print a line every so often."""
        with self._lock:
            self._done += 1
            self._failing += failed
            if self._done % self._step and self._done != self._total:
                return
            elapsed = time.monotonic() - self._started
            rate = self._done / elapsed if elapsed else 0.0
            left = (self._total - self._done) / rate if rate else 0.0
            print(f"  {self._done}/{self._total} comprobados · "
                  f"{self._failing} KO · {rate:.0f} mapas/s · "
                  f"~{left:.0f}s restantes", flush=True)


class SuiteRunner:
    """Runs the solver over every map and judges what it printed.

    Each map is an independent subprocess, so they are checked several at a
    time; results are put back into map order before anything is reported,
    which keeps the report identical whatever order they finish in.
    """

    def __init__(self, solver: Solver, timeout: float, jobs: int) -> None:
        self._solver = solver
        self._timeout = timeout
        self._jobs = max(1, jobs)

    def run(self, maps: list[Path], root: Path) -> list[CaseResult]:
        """Check every map; return one result per map, in map order."""
        progress = Progress(len(maps))
        results: list[CaseResult | None] = [None] * len(maps)
        with concurrent.futures.ThreadPoolExecutor(self._jobs) as pool:
            pending = {
                pool.submit(self._check, path, root): index
                for index, path in enumerate(maps)
            }
            for future in concurrent.futures.as_completed(pending):
                outcome = future.result()
                results[pending[future]] = outcome
                progress.tick(not outcome.ok)
        return [item for item in results if item is not None]

    def _check(self, path: Path, root: Path) -> CaseResult:
        """Run one map and validate its schedule; never raises.

        A crash, a timeout and an illegal schedule all come back as a
        failed CaseResult, so one bad map cannot take the run down.
        """
        category = self._category(path, root)
        output = ""
        try:
            game_map = Parser(path.read_text(), path.name).parse()
            output = self._solver.run(path, self._timeout)
            lines = [ln for ln in output.splitlines() if ln.strip()]
            Validator(game_map, lines).validate()
        except MapParseError as err:
            return CaseResult(path, category, False, "mapa_ilegible",
                              str(err), output)
        except InvalidSchedule as err:
            return CaseResult(path, category, False, err.code,
                              err.message, output)
        except OSError as err:
            return CaseResult(path, category, False, "solver_error",
                              str(err), output)
        return CaseResult(path, category, True)

    @staticmethod
    def _category(path: Path, root: Path) -> str:
        """The map's group: its folder under the maps directory."""
        try:
            relative = path.relative_to(root)
        except ValueError:
            return path.parent.name
        return relative.parts[0] if len(relative.parts) > 1 else root.name


# --------------------------------------------------------------------------
# Reporting: everything goes to the screen, nothing to disk.
# --------------------------------------------------------------------------


class Reporter:
    """Prints the verdict: what passed, what failed and why it failed."""

    LABELS = {
        "zona_llena": "zona por encima de su capacidad",
        "enlace_saturado": "conexión por encima de su capacidad",
        "vuelo_sin_aterrizar": "dron en vuelo que no aterriza",
        "aterrizaje_erroneo": "aterriza en una zona que no es su destino",
        "doble_movimiento": "un dron se mueve dos veces en el mismo turno",
        "token_invalido": "token de salida mal formado o desconocido",
        "sin_conexion": "movimiento entre zonas sin conexión",
        "entrada_en_un_turno": "entra en restricted/blocked en un turno",
        "vuelo_hacia_no_restricted": "vuelo hacia una zona no restricted",
        "despegue_en_vuelo": "despega estando todavía en vuelo",
        "posicion_incoherente": "el dron no está donde dice el token",
        "sin_entregar": "quedan drones sin entregar al final",
        "solver_error": "el solver aborta con código de error",
        "timeout": "el solver no termina a tiempo",
        "mapa_ilegible": "el mapa no se pudo leer"
    }

    EXPLANATIONS = {
        "zona_llena":
            "El plan aparca en esa zona más drones de los que caben. Es el "
            "fallo clásico de reservas: entrar en una zona restricted "
            "cuesta 2 turnos (uno en vuelo, otro aterrizando) y durante ese "
            "vuelo la plaza ya está comprometida aunque el dron todavía no "
            "esté dentro. Si el planificador deja despegar a otro dron "
            "hacia esa zona el mismo turno en que uno sale, sin reservar la "
            "plaza de llegada, y aguas abajo hay un cuello más estrecho que "
            "no drena a ese ritmo, la zona acaba con más drones de los "
            "permitidos. La salida se imprime sin error, pero el horario es "
            "ilegal.",
        "enlace_saturado":
            "En ese turno cruzan la conexión más drones que su "
            "max_link_capacity. La capacidad del enlace se cuenta por turno "
            "y sumando los dos sentidos, y hay que reservarla en el "
            "despegue, no en la llegada: un vuelo hacia una zona restricted "
            "ocupa el enlace el turno en que empieza.",
        "vuelo_sin_aterrizar":
            "Un dron salió hacia una zona restricted y al turno siguiente "
            "no aparece aterrizando. Sobre una conexión no se puede "
            "esperar: si la plaza de destino no estaba garantizada para el "
            "turno de llegada, ese despegue nunca fue legal.",
        "aterrizaje_erroneo":
            "El dron estaba en vuelo hacia una zona concreta y el token del "
            "turno siguiente lo coloca en otra. Un vuelo iniciado no se "
            "puede redirigir a mitad de camino.",
        "doble_movimiento":
            "El mismo dron aparece dos veces en la misma línea. Cada dron "
            "hace como mucho un movimiento por turno.",
        "token_invalido":
            "La salida no encaja con el formato del subject: se esperan "
            "tokens D<id>-<zona> o D<id>-<origen>-<destino>, con ids entre "
            "1 y nb_drones y nombres de zona que existan en el mapa. Si "
            "todos los fallos son de este tipo, el problema es de formato "
            "de salida, no de planificación.",
        "sin_conexion":
            "El dron salta entre dos zonas que el mapa no conecta. Las "
            "conexiones son bidireccionales, pero solo existen las que el "
            "mapa declara.",
        "entrada_en_un_turno":
            "El plan entra en una zona restricted con un solo token (cuesta "
            "2 turnos: vuelo y aterrizaje) o entra en una zona blocked, que "
            "es intransitable.",
        "vuelo_hacia_no_restricted":
            "Hay un token de vuelo D<id>-<a>-<b> hacia una zona que no es "
            "restricted. Solo esas cuestan dos turnos; hacia el resto se "
            "llega directamente con un único token.",
        "despegue_en_vuelo":
            "Un dron que ya estaba ocupando una conexión vuelve a despegar. "
            "Primero tiene que aterrizar.",
        "posicion_incoherente":
            "El token dice que el dron vuela por una conexión en la que no "
            "está: su posición según el replay no coincide con ninguno de "
            "los dos extremos.",
        "sin_entregar":
            "Al acabar la salida quedan drones que no están en el end_hub, "
            "o que se quedaron en vuelo. El programa debe terminar cuando "
            "TODOS han llegado.",
        "solver_error":
            "El solver terminó con código distinto de 0 sobre un mapa "
            "válido: excepción no controlada, o rechaza como inválido un "
            "mapa que sí lo es.",
        "timeout":
            "El solver no terminó dentro del límite. Suele indicar un bucle "
            "que no avanza (ningún dron puede moverse y nadie lo detecta) o "
            "una búsqueda con explosión combinatoria.",
        "mapa_ilegible":
            "El propio test no ha podido leer el mapa. Si usas --maps-dir "
            "con mapas tuyos, revisa el formato de ese fichero."
    }

    def __init__(
        self, results: list[CaseResult], elapsed: float, examples: int
    ) -> None:
        self._results = results
        self._elapsed = elapsed
        self._examples = examples

    def print_per_map(self, only_failures: bool) -> None:
        """List every map with its verdict, grouped by category."""
        print()
        print("RESULTADO POR MAPA")
        for category, group in self._by_category().items():
            failed = sum(1 for item in group if not item.ok)
            print(f"\n  [{category}] {len(group)} mapa{_s(len(group))} · "
                  f"{len(group) - failed} OK · {failed} KO")
            for item in group:
                if item.ok:
                    if not only_failures:
                        print(f"    OK  {item.path.stem}")
                else:
                    print(f"    KO  {item.path.stem}  ->  {item.reason}")

    def print_summary(self) -> None:
        """Totals and the final verdict line."""
        failures = [item for item in self._results if not item.ok]
        print()
        print("=" * 70)
        print("RESUMEN")
        print(f"  Mapas comprobados : {len(self._results)}")
        print(f"  OK                : {len(self._results) - len(failures)}")
        print(f"  KO                : {len(failures)}")
        print(f"  Tiempo            : {self._elapsed:.1f}s")
        for category, group in self._by_category().items():
            failed = sum(1 for item in group if not item.ok)
            print(f"    - {category}: {len(group) - failed} OK / "
                  f"{failed} KO")

    def print_diagnosis(self) -> None:
        """Group the failures by cause and explain each cause."""
        failures = [item for item in self._results if not item.ok]
        if not failures:
            return
        print()
        print("=" * 70)
        print("POR QUÉ FALLA")
        for code, group in self._by_code(failures).items():
            label = self.LABELS.get(code, code)
            print(f"\n  [{code}] {len(group)} mapa{_s(len(group))} · "
                  f"{label}")
            print(_wrap(self.EXPLANATIONS.get(code, ""), "    "))
            for case in group[:self._examples]:
                self._print_example(case)

    def print_verdict(self) -> int:
        """Print PASS/FAIL and return the process exit code."""
        failures = [item for item in self._results if not item.ok]
        print()
        print("=" * 70)
        if not failures:
            print("PASS · todos los horarios son legales en los "
                  f"{len(self._results)} mapas.")
            return 0
        print(f"FAIL · {len(failures)} de {len(self._results)} mapas "
              f"producen un horario ILEGAL.")
        print("Nada de esto se ha guardado en disco: si quieres conservarlo, "
              "redirige la salida (> informe.txt).")
        return 1

    def _print_example(self, case: CaseResult) -> None:
        """Show one failing map with its output, so the bug is reproducible."""
        print(f"\n    Ejemplo: {case.category}/{case.path.name}")
        print(f"      Motivo: {case.reason}")
        print("      Mapa:")
        for line in case.path.read_text().splitlines():
            print(f"        | {line}")
        lines = [ln for ln in case.output.splitlines() if ln.strip()]
        if not lines:
            print("      Salida del solver: (vacía)")
            return
        print(f"      Salida del solver ({len(lines)} turnos):")
        for line in lines[:25]:
            print(f"        | {line}")
        if len(lines) > 25:
            print(f"        | ... y {len(lines) - 25} turnos más")

    def _by_category(self) -> dict[str, list[CaseResult]]:
        groups: dict[str, list[CaseResult]] = {}
        for item in self._results:
            groups.setdefault(item.category, []).append(item)
        return dict(sorted(groups.items()))

    @staticmethod
    def _by_code(
        failures: list[CaseResult]
    ) -> dict[str, list[CaseResult]]:
        groups: dict[str, list[CaseResult]] = {}
        for item in failures:
            groups.setdefault(item.code, []).append(item)
        return dict(
            sorted(groups.items(), key=lambda kv: -len(kv[1]))
        )


def _s(count: int) -> str:
    """The Spanish plural 's', so counts of one read properly."""
    return "" if count == 1 else "s"


def _wrap(text: str, indent: str) -> str:
    """Wrap an explanation to a comfortable width, indented."""
    return textwrap.fill(
        text, width=76, initial_indent=indent, subsequent_indent=indent
    )


# --------------------------------------------------------------------------
# Command-line entry point.
# --------------------------------------------------------------------------


class Application:
    """Wires everything together: locate the solver, run, report."""

    def __init__(self, args: argparse.Namespace, here: Path) -> None:
        self._args = args
        self._here = here

    def run(self) -> int:
        """Do the whole job; return the process exit code."""
        maps_dir = self._args.maps_dir.resolve()
        maps = sorted(p.resolve() for p in maps_dir.rglob("*.txt"))
        if not maps:
            print(f"No hay mapas en {maps_dir}/. Copia la carpeta mapas/ "
                  f"junto a este script o usa --maps-dir.", file=sys.stderr)
            return 2
        jobs = self._args.jobs or default_jobs()
        self._print_header(maps_dir, len(maps), jobs)
        locator = SolverLocator(self._here, self._probe_map(maps),
                                self._args.timeout)
        try:
            solver = self._solver(locator)
        except SetupError as err:
            sys.stdout.flush()  # keep the attempts above the error message
            print(f"\nERROR: {err}", file=sys.stderr)
            return 2
        try:
            print(f"\nComando: {solver.template}")
            print(f"Comprobando {len(maps)} mapa{_s(len(maps))} con "
                  f"{jobs} procesos en paralelo...\n")
            started = time.monotonic()
            runner = SuiteRunner(solver, self._args.timeout, jobs)
            results = runner.run(maps, maps_dir)
            elapsed = time.monotonic() - started
        finally:
            locator.cleanup()
        reporter = Reporter(results, elapsed, self._args.examples)
        reporter.print_per_map(self._args.only_failures)
        reporter.print_summary()
        reporter.print_diagnosis()
        return reporter.print_verdict()

    def _print_header(self, maps_dir: Path, total: int, jobs: int) -> None:
        print("=" * 70)
        print(f"Fly-In · test de estrés de horarios v{__version__}")
        print("=" * 70)
        print(f"Proyecto  : {self._here}")
        print(f"Mapas     : {total} en {maps_dir}/")
        print(f"Paralelo  : {jobs} procesos · timeout "
              f"{self._args.timeout:g}s por mapa")
        print("\nDetectando cómo ejecutar el solver...")

    def _solver(self, locator: SolverLocator) -> Solver:
        """The solver command: the one given, or the one auto-detected."""
        if self._args.cmd:
            print("  · usando el comando indicado con --cmd")
            return Solver(label=self._args.cmd, template=self._args.cmd)
        return locator.locate()

    @staticmethod
    def _probe_map(maps: list[Path]) -> Path:
        """The cheapest map, used to check a candidate command works."""
        return min(maps, key=lambda path: path.stat().st_size)


def default_jobs() -> int:
    """How many maps to check at once when --jobs is not given.

    The work is one subprocess per map, so it is the machine's cores, not
    this process, that do the work; a thread per core keeps them all fed.

    Returns:
        One job per CPU, capped so a very large machine does not drown the
        scheduler in solver processes.
    """
    return min(32, os.cpu_count() or 1)


def build_parser(here: Path) -> argparse.ArgumentParser:
    """The command-line interface, documented in Spanish."""
    parser = argparse.ArgumentParser(
        description="Ejecuta un solver de Fly-In sobre una batería de mapas "
                    "y valida cada horario con un validador independiente. "
                    "No escribe nada en el proyecto."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"fly-in stress test {__version__}"
    )
    parser.add_argument(
        "--cmd",
        help="comando del solver; {map} se sustituye por la ruta de cada "
             "mapa (si no aparece, se añade al final). Solo hace falta si "
             "la detección automática no acierta"
    )
    parser.add_argument(
        "--maps-dir",
        type=Path,
        default=here / "mapas",
        metavar="DIR",
        help="carpeta de mapas, recorrida en profundidad (por defecto: "
             "mapas/ junto a este script)"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        metavar="N",
        help=f"cuántos mapas comprobar a la vez (por defecto: uno por "
             f"núcleo, aquí {default_jobs()}; --jobs 1 va en serie)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        metavar="SEG",
        help="segundos máximos por mapa (por defecto: 10)"
    )
    parser.add_argument(
        "--only-failures",
        action="store_true",
        help="en el listado por mapa, mostrar solo los KO"
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=1,
        metavar="N",
        help="cuántos ejemplos completos (mapa + salida) mostrar por cada "
             "causa de fallo (por defecto: 1; 0 los oculta)"
    )
    return parser


def main(argv: list[str]) -> int:
    """Parse the arguments and run the battery."""
    here = Path(__file__).resolve().parent
    args = build_parser(here).parse_args(argv)
    return Application(args, here).run()


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main(sys.argv[1:]))
