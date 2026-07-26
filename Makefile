# Root orchestrator. It does NOT implement anything itself: each subproject owns
# its own toolchain and Makefile, and this file only delegates to them.
#
#   backend/  -> Python toolchain (uv, pytest, mypy, flake8), see backend/Makefile
#   frontend/ -> React/npm toolchain (added here when the frontend is born)
#
# So `make test` at the repo root runs the backend suite today, and will also run
# the frontend suite once frontend/ exists — without this file learning how either
# toolchain works internally.

.PHONY: install run lint lint-strict type test quality clean

install:
	$(MAKE) -C backend install

run:
	$(MAKE) -C backend run ARGS="$(ARGS)"

lint:
	$(MAKE) -C backend lint

lint-strict:
	$(MAKE) -C backend lint-strict

type:
	$(MAKE) -C backend type

test:
	$(MAKE) -C backend test

quality:
	$(MAKE) -C backend quality

clean:
	$(MAKE) -C backend clean
