"""Headless tests of the Streamlit script, using Streamlit's own AppTest harness."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "thilibudget" / "app.py")


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("THILIBUDGET_SAVE", str(tmp_path / "budget.json"))
    return AppTest.from_file(APP, default_timeout=10).run()


def add(app, kind, amount, category):
    app.radio[0].set_value(kind)
    app.text_input[0].set_value(amount)
    app.text_input[1].set_value(category)
    app.button[0].click().run()
    return app


def test_starts_empty(app):
    assert not app.exception
    assert app.metric[0].value == "0.00"


def test_state_survives_a_rerun(app):
    add(app, "income", "1000", "salary")
    assert app.metric[0].value == "1,000.00"
    app.run()  # a rerun re-executes the whole script; the account must still be there
    assert app.metric[0].value == "1,000.00"


def test_domain_errors_become_messages_not_tracebacks(app):
    add(app, "expense", "50", "food")  # empty account, overdraft refused
    assert not app.exception
    assert any("cannot cover" in e.value for e in app.error)
    assert app.metric[0].value == "0.00"


def test_bad_input_is_a_message(app):
    add(app, "income", "lots", "salary")
    assert not app.exception and any("amount must be a number" in e.value for e in app.error)


def test_saved_state_loads_on_next_session(tmp_path, monkeypatch):
    monkeypatch.setenv("THILIBUDGET_SAVE", str(tmp_path / "budget.json"))
    add(AppTest.from_file(APP, default_timeout=10).run(), "income", "42", "gift")
    assert AppTest.from_file(APP, default_timeout=10).run().metric[0].value == "42.00"


def test_corrupt_save_is_a_warning_not_a_crash(tmp_path, monkeypatch):
    (tmp_path / "budget.json").write_text("not json")
    monkeypatch.setenv("THILIBUDGET_SAVE", str(tmp_path / "budget.json"))
    app = AppTest.from_file(APP, default_timeout=10).run()
    assert not app.exception and app.warning and (tmp_path / "budget.json.corrupt").exists()
