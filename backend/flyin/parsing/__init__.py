"""Parsing layer: turn raw map text into domain objects.

This layer depends on ``domain`` but not the other way around. Parse errors are
reported with a clear message so a malformed map stops the program instead of
producing a silently wrong world.
"""
