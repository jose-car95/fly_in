"""Pathfinding layer: shortest routes over the traversable graph.

This layer depends on ``graph`` and ``domain`` (it reads the adjacency and the
per-zone move cost) but not on anything above it. It answers "what is the
cheapest route from start to end, and is there one at all?" with Dijkstra.
"""
