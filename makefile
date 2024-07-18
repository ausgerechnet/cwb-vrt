install:
	python -m venv venv && \
	. venv/bin/activate && \
	python -m pip install -r requirements.txt

test:
	. venv/bin/activate && \
	pytest -s -v
