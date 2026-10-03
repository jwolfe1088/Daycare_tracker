# Daycare Tracker

A simple Python + SQLite tool to replace the Google Sheets workaround for tracking
client bookings, prepay pack balances, and daily check-ins.

## Daily Use - The Easy Way

You don't need to write any Python code day to day. Just run the menu app:

```
python3 app.py
```

This gives you a numbered menu — add clients, check dogs in, view balances, see who's
checked in today, view low-balance clients needing repurchase, and more. Type the number
of what you want to do and follow the prompts.

## Setup (do this once)

1. **Install Python** if it's not already on the computer you're using (your ThinkPad
   already has it from your Docker setup). Check by opening a terminal and typing:
   ```
   python3 --version
   ```
   If that shows a version number, you're set.

2. **Put this whole folder somewhere permanent** on your computer — for example
   `Documents/daycare_tracker/`. Keep all four files together: `app.py`, `daycare.py`,
   `schema.py`, `README.md`, and the `daycare.db` file once it's created.

3. **Open a terminal in that folder.** In VS Code: File > Open Folder, select this folder,
   then open a terminal with View > Terminal.

4. **Run the app:**
   ```
   python3 app.py
   ```

That's it — the menu takes over from there.

## Using it across your two computers

Since you already sync between home and work with Git, you could put this folder in a Git
repo to keep it in sync. One important thing to know: `daycare.db` is your actual data —
back it up regularly (just copy the file somewhere safe, like a USB drive or cloud folder)
so you never lose client/booking history.



## Using the functions directly (advanced/optional)

If you ever want to script something custom instead of using the menu, the functions
are all available to import directly:

```python
from daycare import *

# Add a new client and their dog(s)
client_id = add_client("Sarah Johnson", "614-555-0123", "sarah@email.com")
dog_id_1 = add_dog(client_id, "Buddy")
dog_id_2 = add_dog(client_id, "Max")

# Client buys a prepay pack (adds to existing balance, doesn't replace it)
# purchase_pack(client_id, dog_count, days) - looks up the correct price automatically
purchase_pack(client_id, 2, 10)  # 2-dog, 10-day pack - logs the purchase and price paid

# Check in dogs for the day
check_in(client_id, [dog_id_1, dog_id_2], "prepay")          # both dogs, full day
check_in(client_id, [dog_id_1], "prepay")                    # only 1 of 2 dogs - auto deducts 0.5 day

# Daily-pay client (no prepay balance)
client2 = add_client("Tom Lee", "614-555-0456")
dog3 = add_dog(client2, "Rex")
check_in(client2, [dog3], "daily")                            # logs as unpaid, $26 charged

# Edit a client's info (only fields you provide get changed)
update_client(client_id, email="newemail@example.com")

# Fix a dog's name
update_dog_name(dog_id_1, "Buddy Jr")

# Manually correct a balance if something got out of sync
adjust_balance(client_id, 7.5)

# Check a client's prepay balance
get_balance(client_id)

# See who's checked in today (or pass a date string "YYYY-MM-DD")
whos_here_today()

# See clients running low / negative on their prepay balance - check this regularly!
low_balance_clients(threshold=1.0)

# At end of week, see what a daily-pay client owes for unpaid visits (just the total)
get_unpaid_total(client2, "2026-06-29", "2026-07-05")

# Better - see the full breakdown: which dates, how many days, total owed
get_unpaid_visits(client2, "2026-06-29", "2026-07-05")

# Check who is still on-site (checked in but not checked out) for a date
whos_still_here()

# Check a dog out - returns details so you know if payment still needs handling
check_out_dog(dog_id_1)

# If you have a checkin_id (returned by check_out_dog) and want to mark just that visit paid
mark_single_checkin_paid(checkin_id)

# Mark every unpaid visit for a client as paid, regardless of date (e.g. they pay you in full at pickup)
mark_all_unpaid_paid(client2)
```

## Pricing rules currently built in

- 1 dog, daily pay: $26/day
- 2 dogs, daily pay: $42/day
- 2-dog pack, only 1 dog shows up that day: charged/deducted at half the 2-dog rate ($21 or 0.5 day)
- Prepay packs never reset to a new number when repurchased — new days always **add** to
  whatever balance is currently there, even if negative.

**Package prices:**

| Package | Price |
|---|---|
| 1 dog, 5 days | $117.00 |
| 1 dog, 10 days | $227.00 |
| 1 dog, 20 days | $442.00 |
| 2 dogs, 5 days | $205.00 |
| 2 dogs, 10 days | $360.00 |
| 2 dogs, 20 days | $672.00 |

Every pack purchase is logged in the `purchases` table with the price actually paid, so you
have a record of pack revenue over time if you ever want to pull it.

If pricing ever changes, update the rate variables and `PACKAGE_PRICES` dictionary at the
top of `daycare.py`.

## Files

- `app.py` — the menu app you'll actually run day to day
- `schema.py` — creates the database and tables (run once, or after a reset)
- `daycare.py` — all the core functions (add clients/dogs, check in, balances, reports)
- `daycare.db` — the actual database file holding all your data (back this up regularly!)
