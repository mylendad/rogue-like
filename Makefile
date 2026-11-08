VENV ?= .venv
PYTHON_VERSION ?= 3.10
PYTHON ?= $(VENV)/bin/python
UV ?= uv

.PHONY: install uninstall run test

install:
	$(UV) venv $(VENV) --python $(PYTHON_VERSION) --allow-existing
	$(UV) pip install --python $(PYTHON) pytest ruff

uninstall:
	rm -rf $(VENV) .pytest_cache .ruff_cache .pyright
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

run:
	$(PYTHON) src/main.py

test:
	$(PYTHON) -m pytest
