"""CLI adapter: the command-line front-end over the application use case.

A thin adapter that turns a map file into text, hands it to ``FlyinSolver`` and
renders the result to stdout, with errors on stderr. It never parses or
simulates itself. The engine and use case know nothing about it, so an API or a
UI can drive the same use case as sibling adapters.
"""
