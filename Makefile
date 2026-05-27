.PHONY: sync lint test agent inspector

sync:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	cd expense-tracker && uv run pytest

agent:
	cd expense-agent && uv run python main.py

inspector:
	cd expense-tracker && uv run mcp dev server.py
