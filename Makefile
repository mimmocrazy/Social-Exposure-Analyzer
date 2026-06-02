.PHONY: test backend b frontend f

test:
	python scripts/run_all_tests.py

backend: b
b:
	python -m uvicorn backend.main:app --reload --port 8000

frontend: f
f:
	cd frontend && npm run dev
 