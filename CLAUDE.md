# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make sync       # uv sync — install all deps
make lint       # ruff check + format --check
make test       # pytest (expense-tracker/tests/)
make agent      # run the CLI chatbot
make inspector  # MCP Inspector UI for expense-tracker

# Add dep to a specific package
cd expense-agent && uv add some-package   # updates root uv.lock
```

Run tests: `cd expense-tracker && uv run pytest`

## Architecture

uv workspace — two packages, one shared `.venv` at root, one `uv.lock`.

```
You (natural language)
        │
        ▼
  expense-agent/          ← Pydantic AI + OpenRouter
    agent.py              ← Agent def, MCPToolset, system prompt
    main.py               ← asyncio CLI loop, message_history accumulation
        │
        │ stdio (subprocess)
        ▼
  expense-tracker/        ← FastMCP server
    server.py             ← @mcp.tool() wrappers only, no SQL
    db.py                 ← pure SQLite, no MCP imports
        │
        ▼
  expense-tracker/expenses.db
```

**Separation contract:** `db.py` has no MCP imports. `server.py` has no SQL. Testable independently.

**MCP tools exposed:** `add_expense`, `list_expenses`, `get_summary` (month filter), `filter_by_category`, `delete_expense`.

**DB schema:** single `expenses` table — `id, amount, real, category text, description text, date text (YYYY-MM-DD), created_at`. Categories stored lowercase.

## Key gotchas

**`load_dotenv()` placement** — must be in `agent.py` (runs at import time), not just `main.py`. `Agent(...)` is instantiated at module level and reads `OPENROUTER_API_KEY` immediately. Moving it breaks startup.

**`EXPENSE_TRACKER_PATH`** — hardcoded as `Path(__file__).parent.parent / "expense-tracker"`. If repo moves, this resolves correctly. If you run `agent.py` from a different cwd, it still works — path is absolute.

**Model override** — set `AGENT_MODEL=openrouter:google/gemini-2.0-flash-exp:free` in `.env` to switch models without touching code. Default `z-ai/glm-4.5-air:free` sometimes ignores tool calls.

**Multi-turn memory** — `result.all_messages()` returns full history (user + assistant + tool calls + tool results). Passed back as `message_history=` each turn. Without this, agent forgets context between turns.
