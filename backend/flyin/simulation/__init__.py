"""Simulation layer: turn-by-turn movement of drones over the map.

This layer depends on ``pathfinding``, ``graph`` and ``domain`` to route the
drones, and produces the exact per-turn output the subject requires. It is the
reusable engine a CLI, an API or a test can drive without the engine knowing
which of them called it.
"""
