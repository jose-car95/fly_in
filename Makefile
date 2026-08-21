.PHONY: install run run-visual serve serve-web debug bench lint lint-strict \
        test quality clean fclean re

BACKEND := backend
UV := uv run --directory $(BACKEND)
MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

install:
	uv sync --directory $(BACKEND)

run:
	uv run --project $(BACKEND) python -m flyin $(ARGS)

run-visual:
	uv run --project $(BACKEND) python -m flyin --visual $(ARGS)

serve:
	uv run --project $(BACKEND) uvicorn \
		flyin.adapters.api.app:create_app \
		--factory --host 127.0.0.1 --port 8000 --reload

serve-web:
	python3 -m http.server 8080 --bind 127.0.0.1 --directory frontend

debug:
	uv run --project $(BACKEND) python -m pdb -m flyin $(ARGS)

bench:
	$(UV) python -m flyin.benchmark

lint:
	$(UV) flake8 .
	$(UV) mypy . $(MYPY_FLAGS)

lint-strict:
	$(UV) flake8 .
	$(UV) mypy . --strict

test:
	$(UV) pytest

quality: lint test

clean:
	find $(BACKEND)/flyin $(BACKEND)/tests -name __pycache__ -exec rm -rf {} +
	rm -rf $(BACKEND)/.mypy_cache $(BACKEND)/.pytest_cache

fclean: clean
	rm -rf $(BACKEND)/.venv

re: fclean install
