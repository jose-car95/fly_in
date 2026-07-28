.PHONY: install run debug clean fclean re lint lint-strict type test quality

install:
	uv sync

run:
	uv run python main.py $(ARGS)

debug:
	uv run python -m pdb main.py $(ARGS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov

fclean: clean
	rm -rf .venv

re: fclean install

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

type:
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

test:
	uv run pytest

quality: lint test
