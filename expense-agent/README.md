# Expense Agent

An AI agent that manages expenses via natural language. Built with Pydantic AI, OpenRouter, and the MCP protocol. Connects to the `expense-tracker` MCP server next door.

---

## What's the difference between MCP and an Agent?

| | MCP Server | Agent |
|---|---|---|
| **What it is** | Tool server — exposes functions | Loop that reasons + calls tools |
| **Who calls it** | Claude Code, Claude Desktop, any MCP client | This Python script |
| **Intelligence** | None — pure functions | LLM decides which tools to call and when |
| **Multi-step** | No — one tool call at a time | Yes — loops until task is done |

The `expense-tracker` (sibling folder) is the MCP server. This project is the agent that *uses* it.

---

## Architecture

```
You (natural language)
        │
        ▼
   main.py  ──────────────────────────────────────────┐
        │                                              │
        ▼                                              │
   Pydantic AI Agent                                   │
   (OpenRouter: z-ai/glm-4.5-air:free)                │
        │                                              │
        │  [ReAct Loop]                                │
        │  1. Reason: which tool to call?              │
        │  2. Act:    call MCP tool                    │
        │  3. Observe: read result                     │
        │  4. Repeat or answer                         │
        │                                              │
        ▼                                              │
   MCP Protocol (stdio)                               │
        │                                             │
        ▼                                             │
   expense-tracker/server.py  (subprocess)           │
        │                                            │
        ▼                                            │
   SQLite (expenses.db)  ◄────────────────────────────┘
```

---

## Project Structure

```
expense-agent/
├── agent.py         # Agent definition — model, MCP server, system prompt
├── main.py          # CLI loop — reads input, runs agent, prints output
├── .env             # OPENROUTER_API_KEY (you create this)
├── .env.example     # Template
└── pyproject.toml
```

**Why two files?**  
`agent.py` defines *what* the agent is. `main.py` defines *how* it's used (CLI). Swap `main.py` for a FastAPI route or a Slack bot later — `agent.py` stays unchanged.

---

## How Pydantic AI Works Here

### 1. MCP server as a subprocess

```python
mcp_server = MCPServerStdio(
    "uv",
    args=["run", "python", "server.py"],
    cwd=EXPENSE_TRACKER_PATH,
)
```

`MCPServerStdio` spawns the expense-tracker server as a child process using stdio pipes. Pydantic AI handles the MCP handshake (initialize → list_tools) automatically.

### 2. Agent with MCP tools

```python
agent = Agent(
    "openrouter:z-ai/glm-4.5-air:free",
    mcp_servers=[mcp_server],
    system_prompt="...",
)
```

When the agent runs, Pydantic AI:
- Discovers all tools from the MCP server
- Converts MCP tool schemas → LLM-compatible function definitions
- Passes them to the model automatically

### 3. The ReAct loop (automatic)

```python
async with agent.run_mcp_servers():           # starts subprocess
    result = await agent.run(user_input,
                             message_history=history)
```

Under the hood, Pydantic AI runs this loop until the model stops calling tools:

```
agent.run(msg)
  │
  ├─ model responds with tool_call → execute via MCP → append result → loop
  ├─ model responds with tool_call → execute via MCP → append result → loop
  └─ model responds with text      → return result
```

You never write this loop yourself.

### 4. Multi-turn conversation

```python
history = result.all_messages()   # save full message history
result2 = await agent.run(next_msg, message_history=history)
```

`all_messages()` returns the full conversation — user messages, assistant messages, tool calls, tool results. Pass it back on the next turn for memory.

---

## Setup

**Prerequisites:** Python 3.13+, [uv](https://docs.astral.sh/uv/), OpenRouter API key, `expense-tracker` sibling folder set up.

```bash
cd expense-agent
uv sync

cp .env.example .env
# edit .env → add your OPENROUTER_API_KEY
```

Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys).

---

## Running

```bash
uv run python main.py
```

Expected output:
```
Expense Agent ready. Type 'quit' to exit.

You: 
```

---

## Example Conversations

**Adding expenses**
```
You: add 450 for lunch under food
Agent: Done! Added ₹450 for "lunch" under food on 2026-05-26.

You: log 1200 uber ride yesterday under transport
Agent: Added ₹1200 for "uber ride" under transport on 2026-05-25.
```

**Viewing expenses**
```
You: show my last 5 expenses
Agent: Here are your last 5 expenses:
  1. ₹1200 — uber ride (transport) — 2026-05-25
  2. ₹450  — lunch (food)          — 2026-05-26
  ...
```

**Summaries**
```
You: summarize my spending for May 2026
Agent: May 2026 summary:
  transport  ₹3400  (4 expenses)
  food       ₹2100  (6 expenses)
  ...

You: which category did I spend most on last month?
Agent: Transport — ₹3400 across 4 expenses.
```

**Multi-turn follow-ups**
```
You: delete that uber ride
Agent: Deleted expense ID 2 (uber ride, ₹1200).
```

The agent remembers the full conversation, so "that uber ride" resolves correctly.

---

## Key Concepts Learned

| Concept | Where |
|---------|-------|
| `Agent("openrouter:model")` — model string format | `agent.py` |
| `MCPServerStdio` — spawns MCP server as subprocess | `agent.py` |
| `mcp_servers=[...]` — auto tool discovery + injection | `agent.py` |
| `agent.run_mcp_servers()` — lifecycle context manager | `main.py` |
| `message_history=` — multi-turn memory | `main.py` |
| ReAct loop — Pydantic AI runs it, you don't write it | internals |
| MCP protocol (initialize, list_tools, call_tool) | hidden by Pydantic AI |

---

## Troubleshooting

**Model doesn't call tools / ignores requests**  
Free models vary in tool-calling reliability. If `z-ai/glm-4.5-air:free` misbehaves, swap the model string in `agent.py`:

```python
# more reliable free alternatives on OpenRouter:
"openrouter:google/gemini-2.0-flash-exp:free"
"openrouter:meta-llama/llama-3.3-70b-instruct:free"
```

**`ModuleNotFoundError: No module named 'agent'`**  
Run from the `expense-agent/` directory: `uv run python main.py`

**expense-tracker server fails to start**  
Check `EXPENSE_TRACKER_PATH` in `agent.py` points to your `expense-tracker` folder. Run `uv sync` inside `expense-tracker/` first.

---

## What's Different From Raw SDK

If you built this with the raw OpenAI/Anthropic SDK, you'd write:

```python
while True:
    response = client.chat.completions.create(model=..., tools=..., messages=history)
    if response.choices[0].finish_reason == "tool_calls":
        for tc in response.choices[0].message.tool_calls:
            args = json.loads(tc.function.arguments)
            result = await mcp_session.call_tool(tc.function.name, args)
            history.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    else:
        break
```

Pydantic AI collapses that entire loop + MCP connection into two lines.  
Trade-off: less control, less to learn about the internals.

---

## Extending This

Ideas to try next:

- **HTTP transport** — swap `MCPServerStdio` for `MCPServerHTTP`, run expense-tracker as a persistent service
- **Multiple MCP servers** — add a second server (e.g., a calendar MCP) to `mcp_servers=[...]`
- **Structured output** — use `Agent(result_type=MyModel)` to get typed Python objects back instead of strings
- **Custom tools** — add `@agent.tool` for logic that doesn't need a separate MCP server
- **Streaming** — `agent.run_stream()` for token-by-token output
