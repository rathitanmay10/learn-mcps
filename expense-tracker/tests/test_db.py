from datetime import date

import db
import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


# --- init_db ---


def test_init_db_idempotent():
    db.init_db()  # second call must not raise or corrupt
    db.init_db()


# --- add_expense ---


def test_add_expense_returns_dict_with_id():
    row = db.add_expense(10.0, "food", "lunch")
    assert row["id"] == 1
    assert row["amount"] == 10.0
    assert row["category"] == "food"
    assert row["description"] == "lunch"


def test_add_expense_defaults_date_to_today():
    row = db.add_expense(5.0, "transport", "bus")
    assert row["date"] == date.today().isoformat()


def test_add_expense_accepts_explicit_date():
    row = db.add_expense(20.0, "food", "dinner", "2024-03-15")
    assert row["date"] == "2024-03-15"


def test_add_expense_lowercases_category():
    row = db.add_expense(10.0, "FOOD", "snack")
    assert row["category"] == "food"


def test_add_expense_raises_on_zero_amount():
    with pytest.raises(ValueError):
        db.add_expense(0, "food", "free")


def test_add_expense_raises_on_negative_amount():
    with pytest.raises(ValueError):
        db.add_expense(-5.0, "food", "refund")


# --- list_expenses ---


def test_list_expenses_returns_newest_first():
    db.add_expense(10.0, "food", "lunch", "2024-01-01")
    db.add_expense(20.0, "food", "dinner", "2024-01-03")
    db.add_expense(5.0, "food", "snack", "2024-01-02")
    rows = db.list_expenses()
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates, reverse=True)


def test_list_expenses_respects_limit():
    for i in range(5):
        db.add_expense(float(i + 1), "food", f"item {i}")
    rows = db.list_expenses(limit=3)
    assert len(rows) == 3


def test_list_expenses_empty():
    assert db.list_expenses() == []


# --- get_summary ---


def test_get_summary_aggregates_by_category():
    db.add_expense(10.0, "food", "a")
    db.add_expense(15.0, "food", "b")
    db.add_expense(30.0, "transport", "c")
    summary = {r["category"]: r["total"] for r in db.get_summary()}
    assert summary["food"] == 25.0
    assert summary["transport"] == 30.0


def test_get_summary_month_filter():
    db.add_expense(100.0, "food", "jan", "2024-01-15")
    db.add_expense(50.0, "food", "feb", "2024-02-10")
    result = db.get_summary(month="2024-01")
    assert len(result) == 1
    assert result[0]["total"] == 100.0


def test_get_summary_empty():
    assert db.get_summary() == []


# --- filter_by_category ---


def test_filter_by_category_returns_matching():
    db.add_expense(10.0, "food", "a")
    db.add_expense(20.0, "transport", "b")
    rows = db.filter_by_category("food")
    assert len(rows) == 1
    assert rows[0]["category"] == "food"


def test_filter_by_category_case_insensitive():
    db.add_expense(10.0, "food", "a")
    rows = db.filter_by_category("FOOD")
    assert len(rows) == 1


def test_filter_by_category_no_match():
    db.add_expense(10.0, "food", "a")
    assert db.filter_by_category("utilities") == []


# --- delete_expense ---


def test_delete_expense_returns_true_on_success():
    row = db.add_expense(10.0, "food", "a")
    assert db.delete_expense(row["id"]) is True


def test_delete_expense_removes_row():
    row = db.add_expense(10.0, "food", "a")
    db.delete_expense(row["id"])
    assert db.list_expenses() == []


def test_delete_expense_returns_false_for_missing_id():
    assert db.delete_expense(9999) is False
