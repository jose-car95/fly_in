# frontend/

**Open door, not built yet.** This folder is reserved for the future React UI and
holds no code today.

## Why it exists already

The `backend/` ↔ `frontend/` split is a deliberate architectural boundary. We
create the folder now — with only this note — so the boundary is visible and the
move is done while the repo is small. Nothing here has real code until the
frontend milestone.

## Its only responsibility (when built)

- Call the backend REST API (`POST /simulate`, `GET /maps`, …).
- Receive JSON and display the simulation.
- **Never** contain business logic: it must not know how routing or scheduling
  work. The simulation engine lives entirely in `backend/`.

## When it is born

After the mandatory CLI project is complete and the backend exposes a stable REST
API. See `docs/PROGRESS.md` for the decision record and the architecture roadmap.
