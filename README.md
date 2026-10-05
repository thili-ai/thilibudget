# thilibudget

A small, hackable budget tracker — transactions, an account that guards its own balance, reports,
JSON persistence that survives a corrupted file, and a Streamlit app that imports a bank statement
without freezing.

> ⚠️ **Educational reference, not production.** A few hundred readable lines, built to be read and
> rebuilt. It keeps one account in one JSON file. For real personal finance use
> [GnuCash](https://gnucash.org/) or [Firefly III](https://www.firefly-iii.org/).

## Built lesson-by-lesson in a Learn Fast course

This is the reference implementation for **Build a Budget Tracker App** (`lfpython-lfbudget`) on
[Learn Fast](https://learnfast.thili.ai), the first drill of the Python Engineer track. You build
these files yourself, one lesson at a time — consult this repo to unblock yourself or to check your
work.

| Lesson | You build | File |
|---|---|---|
| 1 | A working, deliberately clunky expense logger — plain dicts and functions | `examples/lesson1_logger.py` |
| 2 | `Transaction` and `Account`: encapsulation, and why money is `Decimal` | `transaction.py`, `account.py` |
| 3 | `RecurringTransaction` (inheritance) and the abstract `Report` (`abc`) | `transaction.py`, `reports.py` |
| 4 | `MonthlyReport` / `CategoryReport` (polymorphism); the script becomes a package | `reports.py`, `__init__.py` |
| 5 | Exceptions that mean something, and validation that uses them | `exceptions.py`, `account.py` |
| 6 | Persistence: atomic JSON save; a load that survives a missing or corrupt file | `storage.py` |
| 7 | The Streamlit app — and why the account resets on every click until it lives in `session_state` | `app.py` |
| 8 | Importing a bank statement on a background thread | `importer.py`, `app.py` |
| 9 | Exceptions in a GUI and in a thread: where they go, and how to bring them back | `importer.py`, `app.py` |
| 10 | Ship it: deploy, and demonstrate what happens when the save file and the import are broken | `README` of your own repo |

## Quickstart (no keys, no accounts)

```bash
git clone https://github.com/thili-ai/thilibudget && cd thilibudget
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # the package is installed so `streamlit run` can import it

pytest                           # 57 tests
python examples/lesson1_logger.py
streamlit run thilibudget/app.py
```

```python
import datetime as dt
from decimal import Decimal
from thilibudget import Account, Transaction, RecurringTransaction, MonthlyReport

account = Account()
account.add(Transaction(dt.date(2026, 1, 1), Decimal("3000"), "salary"))
rent = RecurringTransaction(dt.date(2026, 1, 3), Decimal("-1100"), "rent", frequency="monthly")
account.add(rent, until=dt.date(2026, 3, 31))     # all three months, or none if one would overdraw
print(MonthlyReport().render(account))
```

## Try the failure modes (lesson 10)

```bash
python examples/make_statement.py big 50000 > data/big_statement.csv   # a slow, successful import
python examples/make_statement.py bad  > data/bad_statement.csv        # error on line 4, shown in the UI
python examples/make_statement.py boom > data/boom_statement.csv       # fails 90% of the way in
echo "{ not json" > budget.json && streamlit run thilibudget/app.py    # kept as budget.json.corrupt
```

## What's inside

- **`Account` is the only way in.** The transaction list and budgets are private; every rule is
  checked *before* anything changes, so a batch either lands whole or not at all.
- **Money is `Decimal`.** `0.1 + 0.2` is `0.30000000000000004` in floats — fine for a distance, not
  for a ledger. Lesson 1's script shows the bug; lesson 2 removes it.
- **Loading never loses good data to bad data.** A missing file is a fresh start; an unreadable one
  is kept as `*.corrupt` (never overwritten); bad records are skipped and reported.
- **The import thread never touches Streamlit.** See below.

### The threading lesson that is not in the Streamlit docs' happy path

Streamlit reruns the whole script on every interaction, so a background thread cannot update the UI
directly. The obvious fix — attach the thread with `add_script_run_ctx` and let it write progress to
`st.session_state` — **fails intermittently**: once a rerun has superseded the script run that
started the thread, the next `session_state` write raises Streamlit's `StopException` *inside the
thread*. It is a `BaseException`, so `except Exception` doesn't catch it, the thread dies silently,
and the UI waits forever on a status nothing will update. (Verified against Streamlit 1.65.0.)

`ImportJob` avoids it: the thread writes to a plain, lock-protected object kept in
`st.session_state`; each rerun of the script *reads* that object. A `finally` guarantees the job can
never be left "running" however the thread ends. `tests/test_importer.py` has a regression test for
exactly this.

Streamlit is pinned (`streamlit==1.65.0`) because its threading internals have moved between
releases — re-verify the pattern before bumping.

## License

MIT © thili.ai
