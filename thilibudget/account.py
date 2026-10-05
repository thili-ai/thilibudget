"""The account (lessons 2-5): encapsulation.

The transaction list and the budgets are private. The only way in is ``add`` / ``add_many`` /
``set_budget``, and those check every rule *before* changing anything — so an account can never
be left half-updated, and nothing outside this class can quietly make the balance wrong.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from decimal import Decimal

from .exceptions import BudgetExceededError, InsufficientFundsError, InvalidTransactionError
from .transaction import Transaction


class Account:
    def __init__(self, name: str = "Main", allow_overdraft: bool = False):
        self.name = name
        self.allow_overdraft = allow_overdraft
        self._transactions: list[Transaction] = []
        self._budgets: dict[str, Decimal] = {}

    # --- reading: always hand out copies, never the private containers ---------------------

    @property
    def balance(self) -> Decimal:
        return sum((t.amount for t in self._transactions), Decimal(0))

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        return tuple(self._transactions)

    @property
    def budgets(self) -> dict[str, Decimal]:
        return dict(self._budgets)

    def spent(self, category: str, year: int, month: int) -> Decimal:
        """Total spent (as a positive number) in one category in one calendar month."""
        return sum(
            (-t.amount for t in self._transactions
             if t.category == category and t.amount < 0
             and (t.date.year, t.date.month) == (year, month)),
            Decimal(0),
        )

    # --- writing ---------------------------------------------------------------------------

    def set_budget(self, category: str, monthly_limit: Decimal) -> None:
        if monthly_limit <= 0:
            raise InvalidTransactionError("a budget limit must be positive")
        self._budgets[category.strip().lower()] = monthly_limit

    def add(self, transaction: Transaction, until: dt.date | None = None) -> list[Transaction]:
        """Add a transaction (or, for a recurring one, every occurrence up to ``until``).

        All-or-nothing: if any occurrence breaks a rule, none are added.
        """
        return self.add_many(transaction.occurrences(until))

    def add_many(self, transactions, *, enforce_limits: bool = True) -> list[Transaction]:
        """Add several transactions atomically.

        ``enforce_limits=False`` is for history that already happened (a bank statement, a save
        file): the bank does not ask your budget's permission, so the rules are not applied.
        """
        batch = sorted(transactions, key=lambda t: t.date)
        if enforce_limits:
            self._check(batch)
        self._transactions.extend(batch)
        return batch

    def _check(self, batch: list[Transaction]) -> None:
        balance = self.balance
        spent: dict[tuple[str, int, int], Decimal] = defaultdict(Decimal)
        for t in batch:
            balance += t.amount
            if t.amount > 0:
                continue
            if not self.allow_overdraft and balance < 0:
                raise InsufficientFundsError(balance - t.amount, -t.amount)
            limit = self._budgets.get(t.category)
            if limit is not None:
                key = (t.category, t.date.year, t.date.month)
                if key not in spent:
                    spent[key] = self.spent(*key)
                spent[key] += -t.amount
                if spent[key] > limit:
                    raise BudgetExceededError(t.category, limit, spent[key])
