"""Importing a bank statement on a background thread (lessons 8-9).

Two jobs, kept apart on purpose:

``parse_statement``  pure, synchronous, easy to test. Raises ``StatementImportError`` with the
                     line number of the first bad row.
``ImportJob``        runs it on a thread and reports through plain, lock-protected attributes.

The thread never touches Streamlit. That is a hard-won rule, not a style choice: writing to
``st.session_state`` from a thread works only while the script run that started it is still
current. Once Streamlit has moved on (every ``st.rerun()`` and every click does), such a write
raises ``StopException`` *inside the thread* — a ``BaseException``, so an ordinary
``except Exception`` does not even see it — and the thread dies without a word while the UI
waits forever on a status that will never change. So instead the job is a plain object, kept
in ``st.session_state`` between reruns; the thread writes to the object, and each rerun of the
script reads from it. It does not touch the ``Account`` either: it hands back parsed
transactions, which the main script adds.

Lesson 9's point lives in ``ImportJob._run``: an exception inside a thread does not reach the
caller. It is printed to the terminal and the thread dies, and the UI shows nothing. So ``_run``
catches everything and relays the failure through the job, and a ``finally`` guarantees the job
never stays "running" if the thread exits some other way.
"""

from __future__ import annotations

import csv
import threading
import time
from collections.abc import Callable

from .exceptions import BudgetError, StatementImportError
from .transaction import Transaction

REQUIRED_COLUMNS = ("date", "description", "amount", "category")
BATCH = 500


def parse_statement(
    text: str,
    on_progress: Callable[[float], None] | None = None,
    throttle: float = 0.0,
) -> list[Transaction]:
    lines = text.splitlines()
    if not lines:
        raise StatementImportError("the file is empty")
    reader = csv.DictReader(lines)
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise StatementImportError(f"missing column(s): {', '.join(missing)}", line=1)

    total = max(len(lines) - 1, 1)
    out: list[Transaction] = []
    for done, row in enumerate(reader, start=1):
        line_no = reader.line_num
        if None in row or None in row.values():
            raise StatementImportError("wrong number of columns", line=line_no)
        try:
            out.append(Transaction.parse(row["date"], row["amount"], row["category"], row["description"]))
        except BudgetError as exc:
            raise StatementImportError(str(exc), line=line_no) from exc
        if done % BATCH == 0:
            if on_progress:
                on_progress(done / total)
            if throttle:
                time.sleep(throttle)
    if on_progress:
        on_progress(1.0)
    return out


class ImportJob:
    """One background import. Safe to read from the main thread while the worker writes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._reset()

    def _reset(self) -> None:
        self._status = "idle"  # idle -> running -> done | failed
        self._progress = 0.0
        self._result: list[Transaction] | None = None
        self._error: str | None = None

    # --- read side (main thread / UI) ---------------------------------------------------
    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def progress(self) -> float:
        with self._lock:
            return self._progress

    @property
    def result(self) -> list[Transaction] | None:
        with self._lock:
            return self._result

    @property
    def error(self) -> str | None:
        with self._lock:
            return self._error

    def reset(self) -> None:
        """Back to idle — call after the result or error has been shown."""
        with self._lock:
            self._reset()

    # --- control -------------------------------------------------------------------------
    def start(self, text: str, throttle: float = 0.0) -> threading.Thread:
        with self._lock:
            if self._status == "running":
                raise RuntimeError("an import is already running")
            self._reset()
            self._status = "running"
        self._thread = threading.Thread(target=self._run, args=(text, throttle), daemon=True)
        self._thread.start()
        return self._thread

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    # --- the worker ----------------------------------------------------------------------
    def _set_progress(self, value: float) -> None:
        with self._lock:
            self._progress = value

    def _run(self, text: str, throttle: float) -> None:
        try:
            result = parse_statement(text, self._set_progress, throttle)
            with self._lock:
                self._result, self._status = result, "done"
        except Exception as exc:  # noqa: BLE001 — deliberately broad: nothing may die silently here
            with self._lock:
                self._error, self._status = f"{type(exc).__name__}: {exc}", "failed"
        finally:
            with self._lock:  # however the thread ends, the UI must never wait forever
                if self._status == "running":
                    self._error, self._status = "the import worker stopped unexpectedly", "failed"
