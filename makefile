install:
	python -m venv venv && \
	. venv/bin/activate && \
	python -m pip install -r requirements-dev.txt

test:
	. venv/bin/activate && \
	pytest -s -v

sdist:
	. venv/bin/activate && \
	python3 setup.py sdist
