# Per il deploy locale:

.PHONY: install setup test backend b frontend f

install: setup
setup:
	@echo "Installazione dipendenze Python in corso..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "Installazione dipendenze Node.js in corso..."
	cd frontend && npm install

test:
	python scripts/run_all_tests.py

backend: b
b:
	python -m uvicorn backend.main:app --reload --port 8000

frontend: f
f:
	cd frontend && npm run dev
 