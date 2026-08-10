"""Shared layer: cross-cutting types used across the other layers.

This layer depends on nothing else in ``flyin`` (every other layer may depend
on it, never the reverse). It holds small, common types such as the parse-error
exception, so that ``parsing`` and any future caller report failures uniformly.
"""
