from decimal import Decimal

import pytest

from thilibudget import StatementImportError
from thilibudget.importer import ImportJob, parse_statement

GOOD = "date,description,amount,category\n2026-01-02,coffee,-3.50,Food\n2026-01-03,pay,1000,salary\n"


def run(text: str, **kw) -> ImportJob:
    job = ImportJob()
    job.start(text, **kw)
    job.join(timeout=5)
    return job


def test_parses_good_csv():
    rows = parse_statement(GOOD)
    assert [r.amount for r in rows] == [Decimal("-3.50"), Decimal("1000")]
    assert rows[0].category == "food"


@pytest.mark.parametrize("text,line", [
    ("", None),
    ("date,amount\n2026-01-01,5\n", 1),
    ("date,description,amount,category\n2026-01-01,x,abc,food\n", 2),
    ("date,description,amount,category\n2026-01-01,x,5,food\n99-99-99,y,5,food\n", 3),
    ("date,description,amount,category\n2026-01-01,x,5\n", 2),
    ("date,description,amount,category\n2026-01-01,x,5,food,extra\n", 2),
])
def test_malformed_input_names_the_line(text, line):
    with pytest.raises(StatementImportError) as err:
        parse_statement(text)
    assert err.value.line == line


def test_progress_is_reported_in_batches():
    big = "date,description,amount,category\n" + "2026-01-01,x,-1,misc\n" * 1200
    seen: list[float] = []
    parse_statement(big, seen.append)
    assert seen[0] == pytest.approx(500 / 1200) and seen[-1] == 1.0


def test_a_fresh_job_is_idle():
    job = ImportJob()
    assert (job.status, job.progress, job.result, job.error) == ("idle", 0.0, None, None)


def test_thread_reports_success():
    job = run(GOOD)
    assert job.status == "done" and len(job.result) == 2
    assert job.progress == 1.0 and job.error is None


def test_exception_in_thread_is_relayed_not_lost():
    job = run("date,description,amount,category\n2026-01-01,x,abc,food\n")
    assert job.status == "failed" and job.result is None
    assert "StatementImportError" in job.error and "line 2" in job.error


def test_unexpected_exception_is_also_relayed(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("disk on fire")
    monkeypatch.setattr("thilibudget.importer.parse_statement", boom)
    job = run(GOOD)
    assert job.status == "failed" and "disk on fire" in job.error


class Stop(BaseException):
    """Like Streamlit's StopException: not an Exception, so `except Exception` never sees it."""


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_a_thread_killed_by_a_baseexception_still_ends_failed(monkeypatch):
    # The bug this guards against: the worker dies silently and the UI waits on "running" forever.
    def die(*a, **k):
        raise Stop()
    monkeypatch.setattr("thilibudget.importer.parse_statement", die)
    job = run(GOOD)
    assert job.status == "failed" and "stopped unexpectedly" in job.error


def test_cannot_start_two_imports_at_once():
    job = ImportJob()
    job.start(GOOD, throttle=0)  # finishes instantly, so force the state
    job.join(5)
    job._status = "running"  # noqa: SLF001
    with pytest.raises(RuntimeError):
        job.start(GOOD)


def test_reset_returns_to_idle():
    job = run(GOOD)
    job.reset()
    assert job.status == "idle" and job.result is None


def test_the_importer_does_not_import_streamlit():
    import thilibudget.importer as importer
    source = open(importer.__file__).read()
    assert "import streamlit" not in source and "from streamlit" not in source
