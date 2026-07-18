.PHONY: install run debug clean lint lint-strict type test quality

install:
	python -m pip install -e ".[dev]"

run:
	python main.py $(ARGS)

debug:
	python -m pdb main.py $(ARGS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

type:
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

test:
	pytest

quality: lint test
