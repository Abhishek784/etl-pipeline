.PHONY: install run run-fast test lint clean

install:
	pip install -e .
	pip install -r requirements.txt

run:
	python -m pipeline.cli

run-fast:
	python -m pipeline.cli --skip-embeddings

test:
	pytest

lint:
	ruff check src tests

clean:
	rm -rf outputs/*.csv data/warehouse/*.duckdb
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache