import json
from decimal import Decimal

from thilibudget import Account, load, save
from conftest import tx


def test_round_trip(tmp_path, funded):
    funded.add(tx("2026-01-02", "-12.34", "food", "lunch"))
    funded.set_budget("food", Decimal("99"))
    save(funded, tmp_path / "b.json")
    result = load(tmp_path / "b.json")
    assert result.problems == []
    assert result.account.transactions == funded.transactions
    assert result.account.budgets == {"food": Decimal("99")}
    assert not (tmp_path / "b.json.tmp").exists()


def test_missing_file_is_just_a_fresh_start(tmp_path):
    result = load(tmp_path / "nope.json")
    assert result.problems == [] and result.account.balance == 0


def test_garbage_is_quarantined_not_overwritten(tmp_path):
    path = tmp_path / "b.json"
    path.write_text("{ this is not json")
    result = load(path)
    assert result.account.balance == 0 and len(result.problems) == 1
    assert not path.exists() and (tmp_path / "b.json.corrupt").read_text() == "{ this is not json"


def test_wrong_shape_is_quarantined(tmp_path):
    path = tmp_path / "b.json"
    path.write_text("[1, 2, 3]")
    assert (load(path).problems) and (tmp_path / "b.json.corrupt").exists()


def test_bad_records_do_not_cost_the_good_ones(tmp_path, funded):
    save(funded, tmp_path / "b.json")
    data = json.loads((tmp_path / "b.json").read_text())
    data["transactions"] += [
        {"date": "not-a-date", "amount": "5", "category": "x"},
        {"amount": "5"},
        "nonsense",
        {"date": "2026-01-02", "amount": "-40", "category": "food"},
    ]
    (tmp_path / "b.json").write_text(json.dumps(data))
    result = load(tmp_path / "b.json")
    assert len(result.problems) == 3
    assert result.account.balance == Decimal("960")


def test_loading_history_ignores_overdraft_rule(tmp_path):
    a = Account()
    a.add_many([tx("2026-01-01", "-5")], enforce_limits=False)
    save(a, tmp_path / "b.json")
    assert load(tmp_path / "b.json").account.balance == Decimal("-5")
