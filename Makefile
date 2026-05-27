.PHONY: sync lint test agent inspector cli

sync:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format .

test:
	cd expense-tracker && uv run pytest

agent:
	cd expense-agent && uv run python main.py

inspector:
	cd expense-tracker && uv run mcp dev server.py

cli:
	cd expense-tracker && uv run python cli.py $(ARGS)
