.PHONY: install test lint run build-data

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn app.api.main:app --reload

# Merge raw datasets in data/raw into data/processed/merged.csv (see data/README.md)
build-data:
	python scripts/build_dataset.py --raw data/raw --out data/processed/merged.csv
