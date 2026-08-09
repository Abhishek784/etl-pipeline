.PHONY: help install run run-fast test test-fast lint format warehouse shell clean clean-all verify

help:
	@echo "install    Install the package and dependencies"
	@echo "run        Build all tables, write outputs/*.csv, load DuckDB"
	@echo "run-fast   As above, CSV only (no DuckDB, no embeddings)"
	@echo "test       Full test suite"
	@echo "test-fast  Unit tests only, skipping the pipeline fixtures"
	@echo "query      Open a DuckDB shell against the warehouse"
	@echo "verify     Clean rebuild from scratch, then test"
	@echo "clean      Remove generated outputs and caches"

install:
	pip install -e .
	pip install -r requirements.txt

run:
	python -m pipeline.cli

run-fast:
	python -m pipeline.cli --skip-embeddings --skip-warehouse

test:
	pytest

test-fast:
	pytest tests/test_revenue.py tests/test_dates.py tests/test_categories.py \
	       tests/test_companies.py tests/test_keys.py

warehouse:
	python -m pipeline.cli --skip-embeddings

query:
	@python -c "\
	import duckdb; \
	con = duckdb.connect('data/warehouse/arr.duckdb'); \
	print(con.sql('SELECT * FROM vw_company_arr_latest ORDER BY arr_usd DESC LIMIT 10'))"

# Prove the pipeline reproduces from nothing -- this is the check that catches
# stale outputs masking a broken build.
verify: clean run test
	@echo "clean rebuild + full suite passed"

clean:
	rm -rf outputs/*.csv
	rm -rf data/warehouse/*.duckdb
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

clean-all: clean
	rm -rf .venv *.egg-info build dist