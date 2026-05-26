# learn-mcps

Learning project for MCP (Model Context Protocol) and AI agents in Python.  
Built in two stages: first an MCP server, then an AI agent that uses it.

---

## What's in Here

```
learn-mcps/
├── .venv/              # shared virtual environment (uv workspace)
├── uv.lock             # single lockfile, deps deduplicated across projects
├── pyproject.toml      # workspace root
├── expense-tracker/    # MCP server — exposes expense tools to any MCP client
└── expense-agent/      # AI agent — uses those tools via natural language
```

These two projects are intentionally separate. The MCP server knows nothing about agents. The agent knows nothing about SQLite. They communicate only through the MCP protocol.

---

## Monorepo Setup (uv Workspace)

This repo uses [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/) — both projects share one venv and one lockfile, but each declares its own dependencies in its own `pyproject.toml`.

```toml
# root pyproject.toml
[tool.uv.workspace]
members = ["expense-tracker", "expense-agent"]
```

**Setup from scratch:**

```bash
git clone <repo>
uv sync          # installs all deps for both projects into root .venv
```

**Run either project:**

```bash
# from root
uv run --package expense-agent python expense-agent/main.py

# or from project dir
cd expense-agent && uv run python main.py
```

**Add a dep to a specific project:**

```bash
cd expense-agent && uv add some-package   # updates root uv.lock automatically
```

---

## The Big Picture

```
You (natural language)
        │
        ▼
  expense-agent          ← AI agent (Pydantic AI + OpenRouter)
  [ReAct loop]           ← reasons, picks tools, observes results
        │
        │  MCP protocol (stdio)
        ▼
  expense-tracker        ← MCP server (FastMCP + SQLite)
  [dumb tool server]     ← no intelligence, just executes functions
        │
        ▼
  expenses.db            ← SQLite database
```

---

## Core Concepts

### MCP (Model Context Protocol)

A standard protocol for AI models to talk to external tools. Like a USB-C standard — build a server once, any MCP-compatible client (Claude Code, Claude Desktop, Cursor, your own agent) can use it.

MCP servers expose three primitive types:
- **Tools** — functions the model can call (what we built)
- **Resources** — data the model can read (files, DB rows, API responses)
- **Prompts** — reusable prompt templates

### AI Agents

An agent is a loop: the model reasons about what to do, calls a tool, observes the result, then decides what to do next — until it has an answer.

```
user message
     │
     ▼
  model (which tool should I call?)
     │
     ├─ tool_call → execute → observe → loop back
     └─ final answer → return to user
```

This is called the **ReAct loop** (Reason + Act). In raw code it's a while loop. Frameworks like Pydantic AI hide it.

---

## Project 1 — expense-tracker (MCP Server)

**Stack:** Python, FastMCP, SQLite  
**Transport:** stdio (Claude spawns server as subprocess)

### What it does

Exposes 5 tools over MCP:

| Tool | Args | What it does |
|------|------|--------------|
| `add_expense` | amount, category, description, date? | Insert expense into DB |
| `list_expenses` | limit? | Recent expenses, newest first |
| `get_summary` | month? (YYYY-MM) | Total per category |
| `filter_by_category` | category | All expenses in a category |
| `delete_expense` | id | Delete by ID |

### File structure

```
expense-tracker/
├── server.py     # MCP layer — @mcp.tool() decorators, thin wrappers
├── db.py         # Data layer — pure SQLite, zero MCP knowledge
└── pyproject.toml
```

### Key design principle

`db.py` has no MCP imports. `server.py` has no SQL. Each layer does one thing. You can test `db.py` standalone without any MCP involved.

### How FastMCP works

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("expense-tracker")

@mcp.tool()
def add_expense(amount: float, category: str, description: str) -> dict:
    """Add a new expense."""          # ← Claude reads this as tool description
    return db.add_expense(...)        # type hints ↑ become JSON schema for args
```

The decorator registers the function as an MCP tool. The docstring becomes the description the model sees. The type hints become the argument schema.

### Running it

```bash
# from repo root — uv sync already done
cd expense-tracker

# Option 1 — MCP Inspector (visual UI to test tools)
uv run mcp dev server.py

# Option 2 — Add to Claude Code ~/.claude/settings.json
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

---

## Project 2 — expense-agent (AI Agent)

**Stack:** Python, Pydantic AI, OpenRouter, FastMCP  
**Model:** `z-ai/glm-4.5-air:free` (via OpenRouter)

### What it does

CLI chatbot. You type natural language. The agent figures out which MCP tools to call, calls them, and responds in plain English. Multi-turn — it remembers the whole conversation.

### File structure

```
expense-agent/
├── agent.py     # Agent definition — model, MCP connection, system prompt
├── main.py      # CLI loop — reads input, runs agent, prints output
└── pyproject.toml
```

### How Pydantic AI wires MCP

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from fastmcp.client.transports import StdioTransport

# 1. Define MCP connection (spawns expense-tracker as subprocess)
mcp_toolset = MCPToolset(
    StdioTransport(command="uv", args=["run", "python", "server.py"], cwd="...")
)

# 2. Create agent — tools auto-discovered from MCP server
agent = Agent("openrouter:z-ai/glm-4.5-air:free", toolsets=[mcp_toolset])
```

At runtime, Pydantic AI:
1. Starts the expense-tracker subprocess
2. Runs the MCP handshake (initialize → list_tools)
3. Converts MCP tool schemas to LLM-compatible function definitions
4. Injects them into every model call
5. Runs the ReAct loop when the model calls a tool
6. Shuts down the subprocess when done

You write none of this — just `async with agent:`.

### Multi-turn memory

```python
history = []

async with agent:
    result = await agent.run("add 500 for lunch", message_history=history)
    history = result.all_messages()   # save full history

    result = await agent.run("delete that", message_history=history)
    # "that" resolves correctly — agent remembers the lunch entry
```

`all_messages()` includes user messages, assistant messages, tool calls, and tool results. The full context is replayed on each turn.

### Setup

```bash
# from repo root — uv sync already done
cd expense-agent

cp .env.example .env
# edit .env → OPENROUTER_API_KEY=sk-or-...
```

Get a free key at [openrouter.ai/keys](https://openrouter.ai/keys).

### Running

```bash
uv run python main.py
```

---

## What Each Project Teaches

### expense-tracker teaches:
- How MCP tools are defined and registered (`@mcp.tool()`)
- How docstrings and type hints become the model's interface
- stdio transport — server lives as a subprocess, talks over stdin/stdout
- Separation of MCP layer from data layer
- Testing tools visually with MCP Inspector

### expense-agent teaches:
- What an AI agent actually is (a loop, not magic)
- How Pydantic AI hides the ReAct loop
- How an agent connects to an MCP server at runtime
- Multi-turn conversation memory via message history
- OpenRouter — one API to access many models
- Python import order gotcha: env vars must load before module-level code runs

---

## What Pydantic AI Hides vs What You'd Write Raw

If you built the agent with raw OpenAI SDK, you'd write this loop yourself:

```python
# Raw SDK — you write this
while True:
    response = client.chat.completions.create(model=..., tools=tools, messages=history)
    if response.choices[0].finish_reason == "tool_calls":
        for tc in response.choices[0].message.tool_calls:
            args = json.loads(tc.function.arguments)
            result = mcp_session.call_tool(tc.function.name, args)
            history.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    else:
        break
```

Pydantic AI collapses that into `await agent.run(...)`. Less to write, less control over internals.

---

## Agent Framework Comparison

| Framework | Best for | Watch out for |
|-----------|----------|----------------|
| **Pydantic AI** | Type-safe agents, MCP-native, clean API | Newer, smaller ecosystem |
| **LangGraph** | Complex multi-agent workflows, stateful graphs | Steep learning curve |
| **LangChain** | Huge integration ecosystem, lots of examples | Heavy abstractions, frequent API changes |
| **CrewAI** | Multi-agent "teams" with roles, fast demos | Thin wrapper over LangChain, hard to debug |
| **Raw SDK** | Maximum control, learning internals | You write the loop yourself |

For production solo agents: Pydantic AI.  
For complex multi-agent orchestration: LangGraph.  
For learning how agents work under the hood: raw SDK.

---

## Troubleshooting

**Model ignores tools / doesn't call them**  
Free models vary in tool-calling reliability. Swap model in `agent.py`:
```python
"openrouter:google/gemini-2.0-flash-exp:free"   # reliable tool use
"openrouter:meta-llama/llama-3.3-70b-instruct:free"
```

**`OPENROUTER_API_KEY` error on startup**  
`load_dotenv()` must be in `agent.py` (runs at import time), not only in `main.py`.

**expense-tracker server fails to start from agent**  
Verify `EXPENSE_TRACKER_PATH` in `agent.py` is correct. Run `uv sync` at repo root first.

**`mcp dev server.py` fails with typer error**  
Needs CLI extras: `uv add "mcp[cli]"` inside `expense-tracker/`.
