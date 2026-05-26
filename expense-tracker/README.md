# Expense Tracker MCP Server

An MCP (Model Context Protocol) server that lets Claude manage your expenses via natural language. Built with Python, FastMCP, and SQLite.

---

## What is MCP?

MCP is a standard protocol that lets AI models like Claude talk to external tools. Think of it as USB-C — you build a server once, and any MCP-compatible client (Claude Code, Claude Desktop, Cursor, etc.) can use it.

```
You (natural language)
        │
        ▼
   Claude (reasons, decides which tool to call)
        │
        ▼
  MCP Server (expense-tracker)
        │
        ▼
   SQLite DB (expenses.db)
```

---

## Project Structure

```
expense-tracker/
├── server.py        # MCP server — exposes tools to Claude
├── db.py            # SQLite layer — all database logic
├── expenses.db      # Auto-created on first run
├── pyproject.toml
└── uv.lock
```

**Why two files?**  
`db.py` has zero MCP knowledge — pure data logic. `server.py` is a thin wrapper that exposes `db.py` functions as MCP tools. Clean separation means you can test DB logic without MCP involved.

---

## Tools Exposed

| Tool | Args | Description |
|------|------|-------------|
| `add_expense` | `amount`, `category`, `description`, `date?` | Add a new expense |
| `list_expenses` | `limit?` (default 20) | Recent expenses, newest first |
| `get_summary` | `month?` (YYYY-MM) | Total spending per category |
| `filter_by_category` | `category` | All expenses in a category |
| `delete_expense` | `id` | Remove an expense by ID |

---

## Setup

**Prerequisites:** Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
git clone <this-repo>
cd expense-tracker
uv sync
```

---

## Usage

### Option 1 — MCP Inspector (test tools visually)

```bash
uv run mcp dev server.py
```

Opens browser at `http://localhost:5173`. Click **Connect**, then call any tool from the UI.

### Option 2 — Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/expense-tracker"
    }
  }
}
```

Restart Claude Code. The server starts automatically as a subprocess.

### Option 3 — Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/expense-tracker"
    }
  }
}
```

Restart Claude Desktop.

---

## Example Conversations

Once connected, talk to Claude naturally:

**Adding expenses**
> "Add ₹450 for lunch, category food"  
> "Log ₹1200 uber ride yesterday under transport"

**Viewing expenses**
> "Show my last 10 expenses"  
> "What did I spend on food this month?"

**Summaries**
> "Summarize my spending for May 2026"  
> "Compare food spending last month vs this month"

**Deleting**
> "Remove expense ID 5, I added it by mistake"

Claude handles intent parsing. The server handles storage. You write zero query logic.

---

## Database Schema

```sql
CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,       -- stored lowercase
    description TEXT    NOT NULL,
    date        TEXT    NOT NULL,       -- YYYY-MM-DD
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

`expenses.db` is created automatically in the project directory on first run.

---

## Key Concepts Learned

| Concept | Where |
|---------|-------|
| `FastMCP` — decorator-based tool registration | `server.py` |
| `stdio` transport — Claude spawns server as subprocess | default in `mcp.run()` |
| Tool docstrings become tool descriptions Claude reads | every `@mcp.tool()` |
| Arg type hints become the JSON schema Claude uses | function signatures |
| Separation of MCP layer vs data layer | `server.py` vs `db.py` |

---

## Extending This

Ideas to add:
- `export_csv` tool — dump expenses to CSV
- `set_budget(category, limit)` + `check_budget()` tools
- HTTP transport instead of stdio (for remote access)
- Resources — expose monthly report as an MCP Resource
