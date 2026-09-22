PYTHON ?= python

.PHONY: server repl client

server:
	$(PYTHON) -m src.server

repl:
	$(PYTHON) -m src.repl

client:
	$(PYTHON) -m src.repl --rpc
