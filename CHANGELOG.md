# Changelog

Historial legible de los cambios del proyecto. Cada entrada explica **qué** cambió y
**por qué**, pensado para revisarlo antes de aprobar una PR — no es un log técnico de git,
es un resumen didáctico.

## [Unreleased] — rama `chore/project-bootstrap`

### 2026-07-18 — Bootstrap inicial del proyecto

El repo solo tenía `.gitignore`, `LICENSE` y un `README.md` vacío. Esta tanda de commits
sube todo el scaffolding necesario para empezar a implementar Fly-In 1.5.

1. **`Update gitignore and README for Fly-In project`**
   Reemplaza el `.gitignore` genérico (plantilla larga, con secciones que no aplican) por
   uno recortado a lo que realmente se usa en un proyecto Python simple. El `README.md`
   pasa de una línea a la plantilla oficial de 42 con las secciones que se rellenarán al
   final (descripción, instrucciones, algoritmo, visualización, recursos).

2. **`Add Python project config: build, lint, test`**
   Añade `pyproject.toml` (paquete `flyin`, Python ≥3.10, dependencias de desarrollo:
   flake8, mypy, pytest), `Makefile` (targets `install`, `run`, `lint`, `type`, `test`,
   `quality`) y `.flake8` (línea máxima 100). Es la base para que `mypy .` y `flake8 .`
   puedan correr sin errores, que es un gate obligatorio antes de dar un slice por
   terminado.

3. **`Add CI workflow for lint and tests`**
   `.github/workflows/ci.yml`: en cada push/PR corre `make lint`, un `lint-strict`
   opcional (mypy --strict, no bloqueante) y `make test`. Esto es lo que protegerá `main`:
   una PR no se puede mergear si estos stages fallan.

4. **`Add Claude Code contract, commands and tutor agent`**
   `CLAUDE.md` documenta el contrato de trabajo con Claude Code: reglas de producto no
   negociables (coste de movimiento, capacidades, stdout exacto, manejo de errores),
   arquitectura por capas (`domain`, `parsing`, `graph/pathfinding`, `scheduling`,
   `simulation`, `cli`) y el flujo de vertical slices. `.claude/commands/` añade
   `/explica`, `/decide`, `/checkrubric` y `/bootstrap-github`; `.claude/agents/tutor.md`
   es un subagente de solo lectura para explicar conceptos sin tocar código.

5. **`Add planning docs: progress, plan, spec notes, evaluation`**
   `docs/PROGRESS.md` (estado vivo del proyecto, milestone actual, decisiones tomadas y
   preguntas abiertas), `docs/PLAN.md` (plan de milestones), `docs/SPEC_NOTES.md`
   (interpretación de las zonas grises del enunciado v1.5) y `docs/EVALUATION.md`
   (rúbrica de defensa con evidencia por ítem). También queda el zip del starter kit
   (`Fly-In_ClaudeCode_Starter_v1_1.zip`) como referencia.

6. **`Add official v1.5 Fly-In map fixtures`**
   Los mapas oficiales adjuntos al enunciado (`maps/easy`, `maps/medium`, `maps/hard`,
   `maps/challenger`), que no se editan nunca — sirven como casos de prueba de referencia
   contra el enunciado real.

7. **`Add edge-case test fixtures`**
   `tests/fixtures/edge-cases/`: mapas mínimos propios (no oficiales) para probar casos
   límite del parser — conexión duplicada invertida, capacidad cero, zona desconocida en
   una conexión, capacidad ignorada en zonas terminales, etc.

8. **`Add GitHub bootstrap script`**
   `scripts/bootstrap_github.sh`: automatiza la creación de labels, issues de M0/M1,
   épicas M2–M6, el Project v2 y la protección de `main`. Se ejecuta una sola vez vía el
   comando `/bootstrap-github`.

9. **`Improve .gitignore for Python workflow (env files, coverage, editors)`**
   El `.gitignore` recortado del primer commit cubría lo básico pero le faltaban casos
   habituales: variables de entorno (`.env`), reportes de cobertura (`coverage.xml`),
   virtualenvs con otro nombre (`env/`) y ruido de editores/SO (`*.swp`, `Thumbs.db`).
   Se agrupó por categorías para que sea fácil de mantener.

### Nota sobre los checks de CI en rojo

Es esperado en este punto: no hay ningún `.py` todavía (M0). `flake8` pasa porque no hay
nada que reportar, pero `mypy` falla con "no .py files" y `pytest` falla con "no tests
ran" — ambos tratan "cero archivos que analizar" como error, no como éxito. En cuanto
exista el primer módulo de dominio con su test, los tres stages deberían ponerse verdes.

### Convención de este fichero

A partir de ahora, cada PR añade su propia entrada aquí (fecha + lista de commits con una
frase de qué/por qué) antes de cerrarse. Sirve como el "formulario" de revisión: léelo
antes de aprobar el merge.
