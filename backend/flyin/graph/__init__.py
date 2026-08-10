"""Graph layer: the traversable adjacency built from a parsed map.

This layer depends on ``domain`` (it reads zones and connections) but not on
``parsing`` or anything above it. It turns the map's zones and connections into
a graph the pathfinding can walk, leaving impassable ``blocked`` zones out.
"""
