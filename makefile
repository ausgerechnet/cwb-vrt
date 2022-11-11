venv:
	python3.9 -m venv .venv

install:
	python3.9 -m pip install -r requirements.txt

test:
	bash .venv/bin/activate && pytest -s -v
