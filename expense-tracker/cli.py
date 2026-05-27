import typer

import db

db.init_db()

app = typer.Typer(help="Expense tracker CLI")


@app.command()
def add(
    amount: float = typer.Argument(..., help="Amount (positive)"),
    category: str = typer.Argument(..., help="Category e.g. food, transport"),
    description: str = typer.Argument(..., help="Short description"),
    date: str = typer.Option(None, "--date", "-d", help="Date YYYY-MM-DD, defaults to today"),
):
    """Add a new expense."""
    if amount <= 0:
        typer.echo("Error: amount must be positive", err=True)
        raise typer.Exit(1)
    row = db.add_expense(amount, category, description, date)
    typer.echo(f"Added  #{row['id']}  {row['date']}  [{row['category']}]  {row['amount']:.2f}  {row['description']}")


@app.command("list")
def list_expenses(
    limit: int = typer.Option(20, "--limit", "-n", help="Max rows to show"),
):
    """List recent expenses."""
    rows = db.list_expenses(limit)
    if not rows:
        typer.echo("No expenses found.")
        return
    typer.echo(f"{'ID':>4}  {'Date':10}  {'Category':12}  {'Amount':>8}  Description")
    typer.echo("-" * 60)
    for r in rows:
        typer.echo(f"{r['id']:>4}  {r['date']:10}  {r['category']:12}  {r['amount']:>8.2f}  {r['description']}")


@app.command()
def summary(
    month: str = typer.Option(None, "--month", "-m", help="Filter month YYYY-MM"),
):
    """Total spending per category."""
    rows = db.get_summary(month)
    if not rows:
        typer.echo("No data.")
        return
    label = f" ({month})" if month else " (all time)"
    typer.echo(f"Summary{label}")
    typer.echo(f"{'Category':12}  {'Total':>8}  Count")
    typer.echo("-" * 32)
    for r in rows:
        typer.echo(f"{r['category']:12}  {r['total']:>8.2f}  {r['count']}")


@app.command()
def filter(
    category: str = typer.Argument(..., help="Category to filter by"),
):
    """List expenses for a specific category."""
    rows = db.filter_by_category(category)
    if not rows:
        typer.echo(f"No expenses in category '{category}'.")
        return
    typer.echo(f"{'ID':>4}  {'Date':10}  {'Amount':>8}  Description")
    typer.echo("-" * 46)
    for r in rows:
        typer.echo(f"{r['id']:>4}  {r['date']:10}  {r['amount']:>8.2f}  {r['description']}")


@app.command()
def delete(
    id: int = typer.Argument(..., help="Expense ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete an expense by ID."""
    if not yes:
        typer.confirm(f"Delete expense #{id}?", abort=True)
    ok = db.delete_expense(id)
    typer.echo(f"Deleted #{id}" if ok else f"No expense with id {id}")


if __name__ == "__main__":
    app()
