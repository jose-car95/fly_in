# Root orchestrator. It does NOT implement anything itself: each subproject owns
# its own toolchain and Makefile, and this file only delegates to them.
#
#   backend/  -> Python toolchain (uv, pytest, mypy, flake8), see backend/Makefile
#   frontend/ -> React/npm toolchain (added here when the frontend is born)
#
# So `make test` at the repo root runs the backend suite today, and will also run
# the frontend suite once frontend/ exists — without this file learning how either
# toolchain works internally.
#
# Cleaning is two-level, mirroring backend/Makefile: each subproject cleans its
# own tree via its Makefile, and the root additionally sweeps repo-root-level
# artifacts that belong to no subproject (e.g. stale caches/.venv left at the top
# level from before the backend/ split). That way `make fclean` from the root
# really leaves a pristine tree, not just a clean backend/.

.PHONY: install run lint lint-strict type test quality clean fclean re

# Repo-root artifacts not owned by any subproject. Kept as make variables so the
# clean/fclean recipes stay short and the intent (light vs heavy) is explicit.
# Only what our toolchain actually creates is listed: caches for clean, and the
# virtualenv for fclean. No build/dist/egg-info — this app never packages itself
# ([tool.uv] package = false), so those are never generated.
ROOT_CACHES := .mypy_cache .pytest_cache .coverage htmlcov
ROOT_HEAVY  := .venv

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

# clean: residual build/test noise. Delegate into backend, then sweep the root.
clean:
	$(MAKE) -C backend clean
	rm -rf $(ROOT_CACHES)

# fclean: back to zero (removes environments too). Delegates backend's own fclean
# (which already runs backend clean) and sweeps every root-level artifact. Kept
# independent from `clean` so backend clean is not invoked twice.
fclean:
	$(MAKE) -C backend fclean
	rm -rf $(ROOT_CACHES) $(ROOT_HEAVY)

# re: rebuild from scratch — a full fclean followed by a fresh install.
re: fclean install
