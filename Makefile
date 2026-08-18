.PHONY: install run bench lint lint-strict type test quality clean fclean re

ROOT_CACHES := .mypy_cache .pytest_cache .coverage htmlcov

install:
	$(MAKE) -C backend install

run:
	$(MAKE) -C backend run ARGS="$(ARGS)"

bench:
	$(MAKE) -C backend bench

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
	rm -rf $(ROOT_CACHES)

fclean:
	$(MAKE) -C backend fclean
	rm -rf $(ROOT_CACHES) .venv

re: fclean install
