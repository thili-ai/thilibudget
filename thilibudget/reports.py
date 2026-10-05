"""Reports (lessons 3-4): abstraction and polymorphism.

``Report`` cannot be instantiated — it has an abstract method, so Python refuses. Callers hold
a ``Report`` and call ``render`` without knowing, or caring, which kind it is.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from decimal import Decimal

from .account import Account


class Report(ABC):
    title = "Report"

    @abstractmethod
    def generate(self, account: Account) -> list[tuple[str, Decimal]]:
        """Return (label, amount) rows. Each subclass decides what the rows mean."""

    def render(self, account: Account) -> str:
        rows = self.generate(account)
        lines = [self.title, "-" * len(self.title)]
        lines += [f"{label:<20}{amount:>14,.2f}" for label, amount in rows]
        if not rows:
            lines.append("(no transactions)")
        return "\n".join(lines)


class MonthlyReport(Report):
    title = "Net by month"

    def generate(self, account: Account) -> list[tuple[str, Decimal]]:
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for t in account.transactions:
            totals[t.date.strftime("%Y-%m")] += t.amount
        return sorted(totals.items())


class CategoryReport(Report):
    title = "Spending by category"

    def generate(self, account: Account) -> list[tuple[str, Decimal]]:
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for t in account.transactions:
            if t.amount < 0:
                totals[t.category] += -t.amount
        return sorted(totals.items(), key=lambda row: row[1], reverse=True)
