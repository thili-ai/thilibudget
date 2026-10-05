import datetime as dt
from decimal import Decimal

import pytest

from thilibudget import Account, Transaction


def tx(day: str, amount: str, category: str = "misc", description: str = "") -> Transaction:
    return Transaction(dt.date.fromisoformat(day), Decimal(amount), category, description)


@pytest.fixture
def funded() -> Account:
    account = Account()
    account.add(tx("2026-01-01", "1000", "salary"))
    return account
