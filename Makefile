PYTHON ?= python

.PHONY: install server repl client test coverage

install:
	$(PYTHON) -m pip install -r requirements.txt

server:
	$(PYTHON) -m src.server

repl:
	$(PYTHON) -m src.repl

client:
	$(PYTHON) -m src.repl --rpc

test:
	$(PYTHON) -m pytest tests

coverage:
	$(PYTHON) -m coverage run --branch --source=src -m pytest tests
	$(PYTHON) -m coverage report -m
