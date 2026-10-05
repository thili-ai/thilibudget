"""Lesson 1: a working expense logger — on purpose a bit clunky.

Plain functions and plain dicts, no classes. It works. Lessons 2-6 make it *better* (a Transaction
class that refuses nonsense, an Account that guards its balance, exceptions that mean something,
a file that survives a crash) — and by the end this script is what you stop writing.

    python examples/lesson1_logger.py
"""


def add(ledger, amount, category, note=""):
    ledger.append({"amount": amount, "category": category, "note": note})


def balance(ledger):
    total = 0
    for entry in ledger:
        total += entry["amount"]
    return total


def show(ledger):
    for number, entry in enumerate(ledger, start=1):
        print(f"{number:>3}  {entry['amount']:>10.2f}  {entry['category']:<12} {entry['note']}")
    print(f"     {'balance':>10}  {balance(ledger):>10.2f}")


def main():
    ledger = []
    print("commands: add <amount> <category> [note] | list | balance | quit")
    print("income is positive, an expense is negative")
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if line == "":
            continue
        words = line.split()
        command = words[0]
        if command == "add" and len(words) >= 3:
            add(ledger, float(words[1]), words[2], " ".join(words[3:]))  # float("abc") crashes us
        elif command == "list":
            show(ledger)
        elif command == "balance":
            print(balance(ledger))  # add 0.1 then 0.2 and look closely: floats are not money
        elif command == "quit":
            break
        else:
            print("sorry, I don't understand that")


if __name__ == "__main__":
    main()
