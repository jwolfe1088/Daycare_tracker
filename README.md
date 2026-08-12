# Daycare Tracker

A Python CLI application for managing daily check-ins, dog profiles, prepay packages, and payment tracking for a small dog daycare business. Originally built to replace a manual spreadsheet workflow, it's now a live production tool handling real client data — and the basis for an integration test suite demonstrating QA automation practices against a real, self-built backend.

![Tests](https://github.com/jwolfe1088/Daycare_tracker/actions/workflows/tests.yml/badge.svg)

## Why this project

Unlike testing an external site through a browser, this project pairs a real CLI application with its own integration test suite, application code and test code living in the same repo, the way they typically do on a real engineering team. It's a different testing style than UI/API automation against third-party sites: driving an interactive terminal program end-to-end, seeding test data directly through application functions, and verifying behavior against the actual database rather than trusting on-screen output alone.

## Tech stack

- **Application:** Python, SQLite
- **Testing:** pytest, `pexpect` (via `popen_spawn.PopenSpawn` for Windows-compatible CLI process spawning)
- **CI:** GitHub Actions — full suite runs automatically on every push

## Test suite highlights

The suite currently covers 8 passing tests across the core workflows: adding clients and dogs, daily check-in/checkout, and cascading deletes for clients and dogs. A few things worth mentioning:

- **Found and documented two real bugs**, discovered through negative testing rather than assumed from the start:
  - Blank client names are silently accepted by the "add client" flow instead of being rejected.
  - Client balance views (`get_balance`, `low_balance_clients`) only track prepay package balances — they never factor in unpaid daily-rate charges, so a client can owe money and still show a $0 balance everywhere except the one report built specifically to catch it.

- **Database-first assertions.** Most tests query the SQLite database directly rather than asserting on printed terminal output, since a success message doesn't prove a write actually happened correctly; the same principle behind checking backend state instead of trusting a UI/API's response alone.

- **Direct function seeding.** Preconditions (like "a client already exists") are set up by calling the application's own functions directly (e.g. `add_client()`), rather than re-driving the CLI through steps already covered by other tests.

- **Isolated test database.** Every test runs against a fresh temporary SQLite file via a pytest fixture, so the suite never touches the real production data.

## Running it

**Setup:**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Run the app:**
```
python app.py
```

**Run the test suite:**
```
pytest -v
```

See [USAGE.md](USAGE.md) for full day-to-day operating instructions, the direct-function reference, and current pricing rules.

## Files

- `app.py` — the interactive CLI menu
- `daycare.py` — core business logic (clients, dogs, check-ins, balances, reports)
- `schema.py` — database schema and migrations
- `tests/` — pytest + pexpect integration test suite
- `.github/workflows/tests.yml` — CI configuration
- `daycare.db` — production database (excluded from version control)