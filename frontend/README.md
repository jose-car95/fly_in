# frontend/

A small web UI (plain HTML, CSS and JavaScript) that talks to the backend
REST API and shows the simulation. It holds **no** business logic: routing and
scheduling live entirely in `backend/`.

## Files

- `index.html` — the page structure.
- `style.css` — the styling.
- `app.js` — calls the API with `fetch` and renders the result into the DOM.

## Running it

The page and the API are served on **different origins**, so the API allows the
page's origin via CORS (see `FRONTEND_ORIGINS` in the backend `app.py`).

```sh
make serve       # API   on http://127.0.0.1:8000
make serve-web   # page  on http://127.0.0.1:8080   (in a second terminal)
```

Then open http://127.0.0.1:8080 in a browser.

## Boundary

- Calls the backend REST API (`GET /api/v1/maps`, `POST /api/v1/simulate`).
- Receives JSON and displays it.
- Never contains business logic. See `docs/PROGRESS.md` for the decisions.
