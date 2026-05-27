from datetime import datetime

import db
from mcp.server.fastmcp import FastMCP

db.init_db()

mcp = FastMCP("expense-tracker")


@mcp.tool()
def add_expense(amount: float, category: str, description: str, date: str | None = None) -> dict:
    """Add a new expense.

    Args:
        amount: Expense amount (positive number)
        category: Category like food, transport, utilities, entertainment
        description: Short description of the expense
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    if date is not None:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"date must be YYYY-MM-DD, got: {date!r}") from None
    return db.add_expense(amount, category, description, date)


@mcp.tool()
def list_expenses(limit: int = 20) -> list[dict]:
    """List recent expenses ordered by date descending.

    Args:
        limit: Max number of expenses to return (default 20)
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    return db.list_expenses(limit)


@mcp.tool()
def get_summary(month: str | None = None) -> list[dict]:
    """Get total spending per category.

    Args:
        month: Filter to specific month in YYYY-MM format. If omitted, returns all-time summary.
    """
    return db.get_summary(month)


@mcp.tool()
def filter_by_category(category: str) -> list[dict]:
    """Get all expenses for a specific category.

    Args:
        category: Category name to filter by (case-insensitive)
    """
    return db.filter_by_category(category)


@mcp.tool()
def delete_expense(id: int) -> dict:
    """Delete an expense by ID.

    Args:
        id: The expense ID to delete
    """
    deleted = db.delete_expense(id)
    return {"deleted": deleted, "id": id}


if __name__ == "__main__":
    mcp.run()
