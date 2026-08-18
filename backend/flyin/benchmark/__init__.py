"""Benchmark harness: measure makespan and validity per map.

A development-facing layer (not the mandatory CLI) that drives the engine and
the independent validator to measure each map against the subject's turn
targets. Depends inward on domain, parsing and simulation; nothing depends on
it.
"""
