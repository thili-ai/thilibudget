import datetime as dt
from decimal import Decimal

import pytest

from thilibudget import InvalidTransactionError, RecurringTransaction, Transaction
from conftest import tx


def test_kind_follows_the_sign():
    assert tx("2026-01-01", "5").kind == "income"
    assert tx("2026-01-01", "-5").kind == "expense"


@pytest.mark.parametrize("amount", ["0", "NaN", "Infinity"])
def test_rejects_unusable_amounts(amount):
    with pytest.raises(InvalidTransactionError):
        tx("2026-01-01", amount)


def test_rejects_empty_category():
    with pytest.raises(InvalidTransactionError):
        Transaction(dt.date(2026, 1, 1), Decimal("5"), "   ")


def test_rejects_float_money():
    with pytest.raises(InvalidTransactionError):
        Transaction(dt.date(2026, 1, 1), 5.0, "misc")  # type: ignore[arg-type]


def test_parse_normalises_and_wraps_errors():
    t = Transaction.parse(" 2026-03-15 ", " -12.50 ", " Groceries ", " milk ")
    assert (t.date, t.amount, t.category, t.description) == (
        dt.date(2026, 3, 15), Decimal("-12.50"), "groceries", "milk")
    for bad in [("15/03/2026", "5"), ("2026-03-15", "five")]:
        with pytest.raises(InvalidTransactionError):
            Transaction.parse(*bad, "x")


def test_decimal_money_adds_exactly():
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")


def test_transactions_are_immutable():
    with pytest.raises(Exception):
        tx("2026-01-01", "5").amount = Decimal("6")  # type: ignore[misc]


def test_a_plain_transaction_occurs_once():
    t = tx("2026-01-01", "5")
    assert t.occurrences(dt.date(2027, 1, 1)) == [t]


def test_recurring_is_a_transaction():
    assert issubclass(RecurringTransaction, Transaction)


def test_monthly_occurrences_clamp_then_recover():
    rent = RecurringTransaction(dt.date(2026, 1, 31), Decimal("-100"), "rent", frequency="monthly")
    days = [t.date for t in rent.occurrences(dt.date(2026, 4, 30))]
    assert days == [dt.date(2026, 1, 31), dt.date(2026, 2, 28), dt.date(2026, 3, 31), dt.date(2026, 4, 30)]


def test_weekly_occurrences():
    gym = RecurringTransaction(dt.date(2026, 1, 1), Decimal("-10"), "gym", frequency="weekly")
    assert len(gym.occurrences(dt.date(2026, 1, 29))) == 5


def test_recurring_defaults_to_one_occurrence_and_rejects_bad_frequency():
    rent = RecurringTransaction(dt.date(2026, 1, 1), Decimal("-5"), "rent")
    assert len(rent.occurrences()) == 1
    assert rent.occurrences(dt.date(2025, 1, 1)) == []
    with pytest.raises(InvalidTransactionError):
        RecurringTransaction(dt.date(2026, 1, 1), Decimal("-5"), "rent", frequency="daily")
