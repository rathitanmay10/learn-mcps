import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "expenses.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                description TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)


def add_expense(
    amount: float, category: str, description: str, expense_date: str | None = None
) -> dict:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if expense_date is None:
        expense_date = date.today().isoformat()
    with get_conn() as conn:
        sql = (
            "INSERT INTO expenses (amount, category, description, date)"
            " VALUES (?, ?, ?, ?) RETURNING *"
        )
        cur = conn.execute(sql, (amount, category.lower(), description, expense_date))
        return dict(cur.fetchone())


def list_expenses(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_summary(month: str | None = None) -> list[dict]:
    """month format: YYYY-MM"""
    with get_conn() as conn:
        if month:
            rows = conn.execute(
                """SELECT category, ROUND(SUM(amount), 2) as total, COUNT(*) as count
                   FROM expenses WHERE strftime('%Y-%m', date) = ?
                   GROUP BY category ORDER BY total DESC""",
                (month,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT category, ROUND(SUM(amount), 2) as total, COUNT(*) as count
                   FROM expenses GROUP BY category ORDER BY total DESC"""
            ).fetchall()
        return [dict(r) for r in rows]


def filter_by_category(category: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC",
            (category.lower(),),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_expense(expense_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cur.rowcount > 0
