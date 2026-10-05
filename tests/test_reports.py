from decimal import Decimal

import pytest

from thilibudget import Account, CategoryReport, MonthlyReport, Report
from conftest import tx


@pytest.fixture
def account():
    a = Account(allow_overdraft=True)
    a.add_many([
        tx("2026-01-01", "1000", "salary"), tx("2026-01-10", "-200", "rent"),
        tx("2026-02-01", "1000", "salary"), tx("2026-02-03", "-50", "food"),
        tx("2026-02-09", "-300", "rent"),
    ])
    return a


def test_report_is_abstract():
    with pytest.raises(TypeError):
        Report()  # type: ignore[abstract]


def test_monthly(account):
    assert MonthlyReport().generate(account) == [("2026-01", Decimal("800")), ("2026-02", Decimal("650"))]


def test_category_orders_biggest_spend_first(account):
    assert CategoryReport().generate(account) == [("rent", Decimal("500")), ("food", Decimal("50"))]


def test_one_interface_two_behaviours(account):
    for report in (MonthlyReport(), CategoryReport()):  # polymorphism: same call, different result
        assert report.title in report.render(account)


def test_empty_account_renders():
    assert "(no transactions)" in MonthlyReport().render(Account())
