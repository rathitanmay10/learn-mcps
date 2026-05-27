import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

load_dotenv()

EXPENSE_TRACKER_PATH = str(Path(__file__).parent.parent / "expense-tracker")

mcp_toolset = MCPToolset(
    StdioTransport(
        command="uv",
        args=["run", "python", "server.py"],
        cwd=EXPENSE_TRACKER_PATH,
    )
)

MODEL = os.getenv("AGENT_MODEL", "openrouter:z-ai/glm-4.5-air:free")

agent = Agent(
    model=MODEL,
    toolsets=[mcp_toolset],
    system_prompt=(
        "You are an expense tracking assistant. "
        "Use the available tools to help the user add, view, summarize, and delete expenses. "
        "Always confirm after tool calls with a brief human-readable summary."
    ),
)
