import datetime as dt
from decimal import Decimal

import pytest

from thilibudget import (
    Account, BudgetExceededError, InsufficientFundsError, InvalidTransactionError,
    RecurringTransaction,
)
from conftest import tx


def test_balance_is_derived_from_transactions(funded):
    funded.add(tx("2026-01-02", "-250.50", "rent"))
    assert funded.balance == Decimal("749.50")


def test_the_outside_cannot_edit_the_ledger(funded):
    funded.transactions  # a copy
    with pytest.raises(AttributeError):
        funded.transactions.append(tx("2026-01-03", "999"))  # type: ignore[attr-defined]
    funded.budgets["rent"] = Decimal(1)
    assert funded.budgets == {}
    assert funded.balance == Decimal("1000")


def test_overdraft_is_refused_with_context(funded):
    with pytest.raises(InsufficientFundsError) as err:
        funded.add(tx("2026-01-02", "-1500"))
    assert err.value.balance == Decimal("1000") and err.value.needed == Decimal("1500")
    assert funded.balance == Decimal("1000")


def test_overdraft_can_be_allowed():
    account = Account(allow_overdraft=True)
    account.add(tx("2026-01-01", "-50"))
    assert account.balance == Decimal("-50")


def test_budget_blocks_the_expense_that_crosses_it(funded):
    funded.set_budget("Food", Decimal("100"))
    funded.add(tx("2026-01-05", "-60", "food"))
    with pytest.raises(BudgetExceededError) as err:
        funded.add(tx("2026-01-06", "-50", "food"))
    assert err.value.category == "food" and err.value.would_be == Decimal("110")
    funded.add(tx("2026-02-01", "-90", "food"))  # a new month starts fresh


def test_bad_budget_limit():
    with pytest.raises(InvalidTransactionError):
        Account().set_budget("food", Decimal("0"))


def test_add_many_is_all_or_nothing(funded):
    batch = [tx("2026-01-02", "-100"), tx("2026-01-03", "-100"), tx("2026-01-04", "-5000")]
    with pytest.raises(InsufficientFundsError):
        funded.add_many(batch)
    assert funded.balance == Decimal("1000") and len(funded.transactions) == 1


def test_history_skips_the_rules(funded):
    funded.add_many([tx("2026-01-02", "-5000")], enforce_limits=False)
    assert funded.balance == Decimal("-4000")


def test_recurring_posts_every_occurrence_or_none(funded):
    rent = RecurringTransaction(dt.date(2026, 1, 1), Decimal("-400"), "rent", frequency="monthly")
    with pytest.raises(InsufficientFundsError):
        funded.add(rent, until=dt.date(2026, 6, 1))  # 6 x 400 > 1000
    assert len(funded.transactions) == 1
    added = funded.add(rent, until=dt.date(2026, 2, 1))
    assert len(added) == 2 and funded.balance == Decimal("200")
