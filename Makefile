.PHONY: install run bench lint lint-strict test quality clean fclean re

BACKEND := backend
UV := uv run --directory $(BACKEND)

install:
	uv sync --directory $(BACKEND)

run:
	uv run --project $(BACKEND) python -m flyin $(ARGS)

bench:
	$(UV) python -m flyin.benchmark

lint:
	$(UV) flake8 .
	$(UV) mypy .

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
