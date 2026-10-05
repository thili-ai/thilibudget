"""Exceptions that carry meaning (lesson 5).

Every error the app raises on purpose derives from ``BudgetError``, so a caller can catch
"anything this library decided was wrong" in one clause — and still catch the specific ones
separately when it wants to react differently.
"""

from decimal import Decimal


class BudgetError(Exception):
    """Base class for every error thilibudget raises deliberately."""


class InvalidTransactionError(BudgetError, ValueError):
    """A transaction's own fields are not acceptable (zero amount, empty category, bad date...)."""


class InsufficientFundsError(BudgetError):
    """An expense would take the balance below zero on an account that forbids overdraft."""

    def __init__(self, balance: Decimal, needed: Decimal):
        self.balance = balance
        self.needed = needed
        super().__init__(f"balance {balance:,.2f} cannot cover an expense of {needed:,.2f}")


class BudgetExceededError(BudgetError):
    """An expense would push a category past its monthly budget."""

    def __init__(self, category: str, limit: Decimal, would_be: Decimal):
        self.category = category
        self.limit = limit
        self.would_be = would_be
        super().__init__(
            f"'{category}' budget is {limit:,.2f} this month; this would make it {would_be:,.2f}"
        )


class StatementImportError(BudgetError):
    """A bank-statement CSV could not be read. ``line`` is the 1-based line of the first problem."""

    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(f"line {line}: {message}" if line else message)
