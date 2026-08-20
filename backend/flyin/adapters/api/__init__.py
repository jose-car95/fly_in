"""HTTP adapter: exposes the reusable engine over a FastAPI app.

A second client of the engine beside the CLI. It depends inward on the
application layer only; the domain never learns that a web server exists.
"""
