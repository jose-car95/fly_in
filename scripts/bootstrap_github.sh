#!/usr/bin/env bash
# Bootstrap de GitHub para Fly-In: labels, issues M0/M1, épicas M2-M6, Project v2,
# campos Status/Flyin Milestone y protección de main. Ejecutar UNA vez desde la raíz del repo,
# con `gh auth login` ya hecho. Requiere: gh, git, python3.
#
# Política de permisos: si un comando gh falla por scope insuficiente, este script se
# detiene e imprime el `gh auth refresh -s <scope>` exacto a ejecutar. No se rodea nada.
set -euo pipefail

fail_scope() {
  echo ""
  echo "ERROR: '$1' ha fallado, probablemente por falta del scope '$2'."
  echo "Ejecuta esto, completa el device flow y relanza el script:"
  echo ""
  echo "    gh auth refresh -s $2"
  echo ""
  exit 1
}

echo "== Comprobando repo y auth =="
gh auth status >/dev/null || { echo "Ejecuta primero: gh auth login"; exit 1; }
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner) || {
  echo "No hay repo remoto. Créalo y vuelve:  gh repo create <nombre> --private --source=. --push"; exit 1; }
OWNER=${REPO%%/*}
echo "Repo: $REPO"

echo "== Labels =="
for L in "parser:1d76db" "sim:0e8a16" "pathfinding:5319e7" "viz:fbca04" "ci:b60205" "docs:c5def5" "epic:d4c5f9"; do
  gh label create "${L%%:*}" --color "${L##*:}" --force >/dev/null && echo "  label ${L%%:*}"
done

echo "== Project v2 =="
PROJ_JSON=$(gh project create --owner "$OWNER" --title "Fly-In" --format json 2>&1) \
  || fail_scope "gh project create" "project"
PROJ_NUM=$(echo "$PROJ_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['number'])")
echo "  Project #$PROJ_NUM creado"

gh project field-create "$PROJ_NUM" --owner "$OWNER" --name "Flyin Milestone" \
  --data-type SINGLE_SELECT --single-select-options "M0,M1,M2,M3,M4,M5,M6" >/dev/null \
  || fail_scope "gh project field-create" "project"
echo "  Campo Flyin Milestone (M0-M6) creado (Status Todo/In Progress/Done ya existe por defecto)"

FIELDS=$(gh project field-list "$PROJ_NUM" --owner "$OWNER" --format json)
PROJ_ID=$(gh project view "$PROJ_NUM" --owner "$OWNER" --format json | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# set_fields <item_id> <milestone M0..M6>  -> Status=Todo y Flyin Milestone
set_fields() {
  python3 - "$1" "$2" << 'PY' | bash
import sys, json, os, subprocess
item, ms = sys.argv[1], sys.argv[2]
fields = json.loads(os.environ["FIELDS"]) ["fields"]
proj = os.environ["PROJ_ID"]
def opt(fname, oname):
    f = next(f for f in fields if f["name"] == fname)
    o = next(o for o in f["options"] if o["name"] == oname)
    return f["id"], o["id"]
sid, soid = opt("Status", "Todo")
mid, moid = opt("Flyin Milestone", ms)
for fid, oid in ((sid, soid), (mid, moid)):
    print(f"gh project item-edit --id {item} --project-id {proj} --field-id {fid} --single-select-option-id {oid}")
PY
}
export FIELDS PROJ_ID

# new_issue <milestone> <labels> <title> <bodyfile>
new_issue() {
  local ms="$1" labels="$2" title="$3" body="$4"
  local url item
  url=$(gh issue create --title "$title" --label "$labels" --body-file "$body")
  item=$(gh project item-add "$PROJ_NUM" --owner "$OWNER" --url "$url" --format json \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
  set_fields "$item" "$ms" >/dev/null
  echo "  [$ms] $title"
}

B=$(mktemp -d)

echo "== Issues M0 =="
cat > "$B/i.md" << 'EOF'
Confirmar Python >=3.10, `make install` funcional y entorno reproducible desde clon limpio.

- [ ] `make install` instala flake8, mypy y pytest
- [ ] `make lint` y `make test` ejecutables (aunque aún no haya código)
- [ ] Rellenar `<login>` en la primera línea del README
EOF
new_issue M0 "ci,docs" "M0: entorno reproducible y Makefile verificado" "$B/i.md"

cat > "$B/i.md" << 'EOF'
Primer vertical slice: test de aceptación en rojo que parsea el mapa mínimo
(`tests/fixtures/edge-cases/valid_minimal.txt`) y representa nb_drones + start/end + conexión.
El test define el contrato; la implementación mínima llega después.
EOF
new_issue M0 "parser" "M0: primer test de aceptación en rojo (mapa mínimo)" "$B/i.md"

echo "== Issues M1 (slices del parser) =="
declare -a M1=(
  "nb_drones + grafo mínimo start/end/conexión"
  "hubs regulares y coordenadas enteras"
  "comentarios/blancos y números de línea físicos en errores"
  "metadatos, defaults y orden libre de tags"
  "unicidad de start/end/nombres; conexiones solo entre zonas definidas"
  "duplicados de conexión no dirigidos (a-b = b-a)"
  "tipos de zona y representación de blocked"
  "validación de capacidades + ignorar max_drones en terminales"
  "errores claros para entradas malformadas"
)
for i in "${!M1[@]}"; do
  echo "Slice $((i+1))/9 del parser (ver docs/PLAN.md M1). Test primero, implementación mínima después." > "$B/i.md"
  new_issue M1 "parser" "M1.$((i+1)): ${M1[$i]}" "$B/i.md"
done

echo "== Issues de decisiones abiertas (SPEC_NOTES) =="
cat > "$B/i.md" << 'EOF'
Fijar el nombre textual exacto del token de conexión en vuelo hacia restricted
(propuesta: `<origen>-<destino>`). Decidir con /decide y registrar en SPEC_NOTES §1.
Bloquea el formateador de salida de M3.
EOF
new_issue M1 "sim,docs" "Decisión: token textual de conexión en vuelo" "$B/i.md"

cat > "$B/i.md" << 'EOF'
Fijar la ventana exacta en que el tránsito restricted consume capacidad del enlace
(¿solo turno de salida o ambos turnos?). Decidir con /decide + tests, registrar en
SPEC_NOTES §1. Bloquea el scheduler de M4.
EOF
new_issue M1 "sim,docs" "Decisión: ventana de capacidad del enlace en tránsito restricted" "$B/i.md"

echo "== Épicas M2-M6 =="
epic() { new_issue "$1" "epic,$2" "$3" "$B/i.md"; }

cat > "$B/i.md" << 'EOF'
Grafo propio y corrección de rutas (ver docs/PLAN.md M2). Se desglosará en issues al llegar.

- [ ] Adyacencia transitable sin librerías; grafos desconexos manejados
- [ ] BFS base
- [ ] Camino mínimo ponderado por coste de destino
- [ ] Desempate determinista y preferencia priority
- [ ] Documentar complejidad
EOF
epic M2 "pathfinding" "Épica M2: grafo propio y corrección de rutas"

cat > "$B/i.md" << 'EOF'
Motor de simulación determinista (ver docs/PLAN.md M3).

- [ ] Máquina de estados del dron
- [ ] Transición atómica SimulationState -> TurnPlan -> SimulationState
- [ ] Movimiento 1 turno y tránsito restricted 2 turnos con llegada obligatoria
- [ ] Retirada de entregados; formateador exacto de salida
- [ ] Validador de schedules independiente
EOF
epic M3 "sim" "Épica M3: motor de simulación determinista"

cat > "$B/i.md" << 'EOF'
Scheduler consciente de capacidad (ver docs/PLAN.md M4).

- [ ] Capacidad 1 por defecto y liberación por salida en el mismo turno
- [ ] max_drones > 1 y capacidades de enlace
- [ ] Reserva futura para llegadas restricted
- [ ] Múltiples caminos, reparto y espera estratégica
- [ ] Prevención/detección de deadlocks
EOF
epic M4 "sim" "Épica M4: scheduler consciente de capacidad"

cat > "$B/i.md" << 'EOF'
Optimización con benchmarks (ver docs/PLAN.md M5).

- [ ] Runner de benchmarks determinista
- [ ] Línea base medida en los 10 mapas oficiales
- [ ] Estimación de makespan de flota y reparto entre caminos
- [ ] Objetivos: Easy -> Medium -> Hard -> individuales -> Challenger <45 (opcional)
- [ ] Tabla de resultados en docs/EVALUATION.md
EOF
epic M5 "pathfinding" "Épica M5: optimización con benchmarks"

cat > "$B/i.md" << 'EOF'
Presentación y endurecimiento para la evaluación (ver docs/PLAN.md M6).

- [ ] Visualización de terminal coloreada sin contaminar stdout
- [ ] README completo con secciones obligatorias y ejemplo
- [ ] Matriz de evaluación con evidencia
- [ ] Ensayo de live coding --capacity-info (<=10 min)
- [ ] Casos límite, mapas inválidos, clon limpio
EOF
epic M6 "viz" "Épica M6: presentación y endurecimiento"

rm -rf "$B"

echo "== Protección de main (stages lint y test obligatorios) =="
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - << 'EOF' >/dev/null || fail_scope "gh api branches/main/protection" "repo"
{
  "required_status_checks": { "strict": true, "contexts": ["lint", "test"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF
echo "  main protegida"

cat << EOF

== HECHO. Pasos manuales en la web (limitación conocida de Projects v2) ==

Las VISTAS y las AUTOMATIZACIONES del Project no se pueden configurar por CLI/API.
Abre el Project "Fly-In" (#$PROJ_NUM) en github.com y haz:

1. Vista principal Board: en la vista por defecto, menú de la pestaña -> Layout: Board
   (columnas por Status). Opcional: Group by -> Flyin Milestone en una copia.
2. Vista secundaria Table: New view -> Table.
3. Automatizaciones (icono ... -> Workflows):
   - "Item added to project" -> Status: Todo   (ON)
   - "Item closed"           -> Status: Done   (ON)
   - "Pull request merged"   -> Status: Done   (ON)
   - "Auto-add to project"   -> repo $REPO, filtro is:issue  (ON)
   NOTA: no existe automatización nativa "PR abierto -> issue a In Progress";
   mover a In Progress es manual al empezar cada issue.

Después pega el resumen de automatizaciones en docs/PROGRESS.md (sección GitHub).
EOF
