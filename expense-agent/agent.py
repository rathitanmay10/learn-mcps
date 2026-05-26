from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from fastmcp.client.transports import StdioTransport
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EXPENSE_TRACKER_PATH = str(Path(__file__).parent.parent / "expense-tracker")

mcp_toolset = MCPToolset(
    StdioTransport(
        command="uv",
        args=["run", "python", "server.py"],
        cwd=EXPENSE_TRACKER_PATH,
    )
)

agent = Agent(
    "openrouter:z-ai/glm-4.5-air:free",
    toolsets=[mcp_toolset],
    system_prompt=(
        "You are an expense tracking assistant. "
        "Use the available tools to help the user add, view, summarize, and delete expenses. "
        "Always confirm after tool calls with a brief human-readable summary."
    ),
)
