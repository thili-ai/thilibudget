"""Generate bank-statement CSVs for lessons 8-10.  Seeded, so everyone gets the same file.

    python examples/make_statement.py big     50000   > data/big_statement.csv
    python examples/make_statement.py bad     > data/bad_statement.csv     (a bad amount on line 4)
    python examples/make_statement.py boom    > data/boom_statement.csv    (fails 90% of the way in)
"""

import datetime as dt
import random
import sys

CATEGORIES = ["groceries", "rent", "transport", "dining", "utilities", "salary", "fun"]
HEADER = "date,description,amount,category"


def rows(n: int, seed: int = 7):
    rng = random.Random(seed)
    day = dt.date(2024, 1, 1)
    for i in range(n):
        category = rng.choice(CATEGORIES)
        cents = rng.randint(200, 9000)
        sign = 1 if category == "salary" else -1
        yield f"{day + dt.timedelta(days=i % 700)},{category} #{i},{sign * cents / 100:.2f},{category}"


mode = sys.argv[1] if len(sys.argv) > 1 else "big"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 50_000
lines = [HEADER, *rows(n if mode == "big" else 1000)]
if mode == "bad":
    lines[3] = "2024-01-03,corrupted row,twelve,groceries"
if mode == "boom":
    lines[int(len(lines) * 0.9)] = "not-a-date,late failure,5,misc"
print("\n".join(lines))
