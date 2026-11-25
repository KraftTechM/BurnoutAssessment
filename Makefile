.PHONY: install run seed test clean

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && uvicorn app.main:app --reload --port 8000

seed:
	. .venv/bin/activate && python scripts/seed_demo.py

test:
	. .venv/bin/activate && pytest

clean:
	rm -f data/burnout.db
