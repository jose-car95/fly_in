"""Application layer: the use cases that orchestrate the domain.

This layer depends on ``parsing`` and ``simulation`` to fulfil a use case
("solve this map into movement lines") but is agnostic to any front-end. The
adapters (``cli`` now, an API later) call into it; it never reaches back out to
them, does no I/O and knows no streams. It is the seam that keeps every
front-end sharing one engine.
"""
