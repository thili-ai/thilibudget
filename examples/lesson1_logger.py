"""Lesson 1: a working expense logger — on purpose a bit clunky.

Plain functions and plain dicts, no classes. It works. Lessons 2-6 make it *better* (a Transaction
class that refuses nonsense, an Account that guards its balance, exceptions that mean something,
a file that survives a crash) — and by the end this script is what you stop writing.

    python examples/lesson1_logger.py
"""

ledger = []  # a list of dicts: {"amount": float, "category": str, "note": str}


def add(amount, category, note=""):
    ledger.append({"amount": amount, "category": category, "note": note})


def balance():
    total = 0
    for entry in ledger:
        total += entry["amount"]
    return total


def show():
    for i, entry in enumerate(ledger, start=1):
        print(f"{i:>3}  {entry['amount']:>10.2f}  {entry['category']:<12} {entry['note']}")
    print(f"     {'balance':>10}  {balance():>10.2f}")


def main():
    print("commands: add <amount> <category> [note...] | list | balance | quit   (expenses are negative)")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split()
        command = parts[0]
        if command == "add" and len(parts) >= 3:
            add(float(parts[1]), parts[2], " ".join(parts[3:]))  # float("abc") will crash us. Lesson 5 fixes that.
        elif command == "list":
            show()
        elif command == "balance":
            print(balance())  # add 0.1 then 0.2 and look closely: floats are not money (lesson 2)
        elif command == "quit":
            break
        else:
            print("?")


if __name__ == "__main__":
    main()
