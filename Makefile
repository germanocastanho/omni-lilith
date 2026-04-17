.PHONY: test lint fmt

test:
	.venv/bin/pytest tests/ -v --asyncio-mode=auto

lint:
	.venv/bin/ruff check .

fmt:
	.venv/bin/ruff format .
