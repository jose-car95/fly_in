"""Adapters layer: the front-ends that drive the application's use case.

Each adapter is a sibling here — ``cli`` now, an API or a UI later. An adapter
translates one outside world (command line, HTTP request, a form) into a call
to the application layer and renders the result back out. Adapters depend
inward on ``application`` (and the domain through it); nothing depends on them,
so adding or removing one never touches the engine.
"""
