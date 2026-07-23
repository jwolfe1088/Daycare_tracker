"""
Core functions for Cheryl's Doggie Daycare tracker.
"""
import sqlite3
from datetime import date

DB_NAME = "daycare.db"

# --- Pricing config - adjust these if rates ever change ---
ONE_DOG_DAILY_RATE = 26.0
TWO_DOG_DAILY_RATE = 42.0
TWO_DOG_PARTIAL_RATE = TWO_DOG_DAILY_RATE / 2  # $21 - one of two dogs from a 2-dog pack

# Package prices: (dog_count, days) -> price
PACKAGE_PRICES = {
    (1, 5): 117.0,
    (1, 10): 227.0,
    (1, 20): 442.0,
    (2, 5): 205.0,
    (2, 10): 360.0,
    (2, 20): 672.0,
}


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    _ensure_checked_out_column(conn)
    return conn


def _ensure_checked_out_column(conn):
    """Safety check: adds the checked_out column if it's missing, without touching existing data."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(checkins)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if "checked_out" not in existing_columns:
        cursor.execute("ALTER TABLE checkins ADD COLUMN checked_out INTEGER DEFAULT 0")
        conn.commit()


def add_client(name, phone="", email=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clients (name, phone, email, balance_days) VALUES (?, ?, ?, 0.0)",
        (name, phone, email),
    )
    conn.commit()
    client_id = cursor.lastrowid
    conn.close()
    print(f"Added client '{name}' (client_id={client_id})")
    return client_id


def add_dog(client_id, dog_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO dogs (client_id, dog_name) VALUES (?, ?)",
        (client_id, dog_name),
    )
    conn.commit()
    dog_id = cursor.lastrowid
    conn.close()
    print(f"Added dog '{dog_name}' for client_id={client_id} (dog_id={dog_id})")
    return dog_id


def purchase_pack(client_id, dog_count, days, purchase_date=None):
    """
    Adds days to a client's existing balance (does not replace it),
    and logs the purchase with the correct price based on dog_count and days.

    dog_count: 1 or 2 (which package pricing tier to use)
    days: 5, 10, or 20
    """
    if purchase_date is None:
        purchase_date = str(date.today())

    price = PACKAGE_PRICES.get((dog_count, days))
    if price is None:
        raise ValueError(f"No package price found for {dog_count} dog(s), {days} days. "
                          f"Valid options: {list(PACKAGE_PRICES.keys())}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clients SET balance_days = balance_days + ? WHERE client_id = ?",
        (days, client_id),
    )
    cursor.execute(
        """INSERT INTO purchases (client_id, purchase_date, dog_count, days, price_paid)
           VALUES (?, ?, ?, ?, ?)""",
        (client_id, purchase_date, dog_count, days, price),
    )
    conn.commit()
    cursor.execute("SELECT balance_days FROM clients WHERE client_id = ?", (client_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()
    print(f"client_id={client_id} purchased {dog_count}-dog/{days}-day pack for ${price:.2f}. "
          f"New balance: {new_balance} days")
    return new_balance


def get_client_dogs(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dog_id, dog_name FROM dogs WHERE client_id = ?", (client_id,))
    dogs = cursor.fetchall()
    conn.close()
    return dogs


def get_balance(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance_days FROM clients WHERE client_id = ?", (client_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def check_in(client_id, dog_ids, payment_type, checkin_date=None):
    """
    Check in one or more dogs for a client on a given day.

    client_id: the client's id
    dog_ids: list of dog_id(s) checking in today (1 or 2 dogs)
    payment_type: "prepay" or "daily"
    checkin_date: defaults to today if not given
    """
    if checkin_date is None:
        checkin_date = str(date.today())

    num_dogs = len(dog_ids)
    total_dogs_owned = len(get_client_dogs(client_id))

    conn = get_connection()
    cursor = conn.cursor()

    if payment_type == "prepay":
        if num_dogs == 2:
            days_deducted = 1.0
            amount_charged = 0.0
        elif num_dogs == 1 and total_dogs_owned == 2:
            # client normally brings 2 dogs on a 2-dog pack, only 1 showed up today
            days_deducted = 0.5
            amount_charged = 0.0
        else:
            days_deducted = 1.0
            amount_charged = 0.0

        cursor.execute(
            "UPDATE clients SET balance_days = balance_days - ? WHERE client_id = ?",
            (days_deducted, client_id),
        )

    elif payment_type == "daily":
        if num_dogs == 2:
            amount_charged = TWO_DOG_DAILY_RATE
        elif num_dogs == 1 and total_dogs_owned == 2:
            amount_charged = TWO_DOG_PARTIAL_RATE
        else:
            amount_charged = ONE_DOG_DAILY_RATE
        days_deducted = 0.0

    else:
        conn.close()
        raise ValueError("payment_type must be 'prepay' or 'daily'")

    for dog_id in dog_ids:
        cursor.execute(
            """INSERT INTO checkins
               (dog_id, client_id, checkin_date, payment_type, days_deducted, amount_charged, paid)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (dog_id, client_id, checkin_date, payment_type,
             days_deducted / num_dogs, amount_charged / num_dogs,
             1 if payment_type == "prepay" else 0),
        )

    conn.commit()
    conn.close()

    print(f"Checked in {num_dogs} dog(s) for client_id={client_id} on {checkin_date} "
          f"({payment_type}) - deducted {days_deducted} day(s), charged ${amount_charged:.2f}")

    if payment_type == "prepay":
        new_balance = get_balance(client_id)
        if new_balance < 0:
            print(f"  WARNING: client_id={client_id} balance is now negative ({new_balance}). Needs repurchase.")


def get_unpaid_total(client_id, start_date, end_date):
    """Sum up unpaid daily-rate charges for a client between two dates (inclusive)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT SUM(amount_charged) FROM checkins
           WHERE client_id = ? AND payment_type = 'daily' AND paid = 0
           AND checkin_date BETWEEN ? AND ?""",
        (client_id, start_date, end_date),
    )
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0.0


def get_unpaid_visits(client_id, start_date, end_date):
    """
    Returns a detailed breakdown of unpaid daily-rate visits for a client
    between two dates (inclusive) - one row per check-in, plus a summary.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT ci.checkin_date, d.dog_name, ci.amount_charged
           FROM checkins ci
           JOIN dogs d ON ci.dog_id = d.dog_id
           WHERE ci.client_id = ? AND ci.payment_type = 'daily' AND ci.paid = 0
           AND ci.checkin_date BETWEEN ? AND ?
           ORDER BY ci.checkin_date""",
        (client_id, start_date, end_date),
    )
    rows = cursor.fetchall()
    conn.close()

    unique_dates = sorted(set(row[0] for row in rows))
    total_owed = sum(row[2] for row in rows)

    print(f"Unpaid visits for client_id={client_id} ({start_date} to {end_date}):")
    for checkin_date, dog_name, amount in rows:
        print(f"  {checkin_date} - {dog_name} - ${amount:.2f}")
    print(f"Total: {len(unique_dates)} day(s), ${total_owed:.2f} owed")

    return {"dates": unique_dates, "num_days": len(unique_dates), "total_owed": total_owed, "visits": rows}


def mark_paid(client_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE checkins SET paid = 1
           WHERE client_id = ? AND payment_type = 'daily'
           AND checkin_date BETWEEN ? AND ?""",
        (client_id, start_date, end_date),
    )
    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()
    print(f"Marked {rows_updated} checkin(s) as paid for client_id={client_id}")


def whos_still_here(checkin_date=None):
    """Dogs checked in but not yet checked out for a given date."""
    if checkin_date is None:
        checkin_date = str(date.today())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT ci.checkin_id, d.dog_id, d.dog_name, c.client_id, c.name,
                  ci.payment_type, ci.paid, ci.amount_charged
           FROM checkins ci
           JOIN dogs d ON ci.dog_id = d.dog_id
           JOIN clients c ON ci.client_id = c.client_id
           WHERE ci.checkin_date = ? AND ci.checked_out = 0""",
        (checkin_date,),
    )
    results = cursor.fetchall()
    conn.close()
    return results


def check_out_dog(dog_id, checkin_date=None):
    """Marks a dog as checked out for the given date (defaults to today)."""
    if checkin_date is None:
        checkin_date = str(date.today())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT checkin_id, client_id, payment_type, paid, amount_charged FROM checkins
           WHERE dog_id = ? AND checkin_date = ? AND checked_out = 0""",
        (dog_id, checkin_date),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        print(f"No active check-in found for dog_id={dog_id} on {checkin_date}.")
        return None

    checkin_id, client_id, payment_type, paid, amount_charged = row
    cursor.execute("UPDATE checkins SET checked_out = 1 WHERE checkin_id = ?", (checkin_id,))
    conn.commit()
    conn.close()
    print(f"Checked out dog_id={dog_id} for {checkin_date}.")
    return {
        "checkin_id": checkin_id, "client_id": client_id, "payment_type": payment_type,
        "paid": paid, "amount_charged": amount_charged,
    }


def mark_single_checkin_paid(checkin_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE checkins SET paid = 1 WHERE checkin_id = ?", (checkin_id,))
    conn.commit()
    conn.close()
    print(f"Marked checkin_id={checkin_id} as paid.")


def mark_all_unpaid_paid(client_id):
    """Marks every unpaid daily-rate checkin for a client as paid, regardless of date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE checkins SET paid = 1 WHERE client_id = ? AND payment_type = 'daily' AND paid = 0",
        (client_id,),
    )
    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()
    print(f"Marked {rows_updated} unpaid checkin(s) as paid for client_id={client_id}")


def check_out_all(checkin_date=None):
    """
    Checks out every dog still checked in for a given date.
    Prepay dogs are deducted automatically, same as individual checkout.
    Returns a list of unpaid daily-rate checkins so the caller can decide how to handle them.
    """
    if checkin_date is None:
        checkin_date = str(date.today())

    still_here = whos_still_here(checkin_date)
    if not still_here:
        print(f"No dogs currently checked in for {checkin_date}.")
        return []

    unpaid_daily = []
    for checkin_id, dog_id, dog_name, client_id, client_name, ptype, paid, amount in still_here:
        check_out_dog(dog_id, checkin_date)
        if ptype == "daily" and not paid:
            unpaid_daily.append({
                "checkin_id": checkin_id, "dog_id": dog_id, "dog_name": dog_name,
                "client_id": client_id, "client_name": client_name, "amount": amount,
            })

    print(f"\nChecked out {len(still_here)} dog(s) for {checkin_date}.")
    return unpaid_daily


def whos_here_today(checkin_date=None):
    if checkin_date is None:
        checkin_date = str(date.today())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT c.name, d.dog_name, ci.payment_type, ci.paid, ci.amount_charged
           FROM checkins ci
           JOIN clients c ON ci.client_id = c.client_id
           JOIN dogs d ON ci.dog_id = d.dog_id
           WHERE ci.checkin_date = ?""",
        (checkin_date,),
    )
    results = cursor.fetchall()
    conn.close()
    return results


def update_client(client_id, name=None, phone=None, email=None):
    """Update one or more fields for a client. Leave a field as None to keep it unchanged."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, phone, email FROM clients WHERE client_id = ?", (client_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        print(f"No client found with client_id={client_id}")
        return

    new_name = name if name else existing[0]
    new_phone = phone if phone else existing[1]
    new_email = email if email else existing[2]

    cursor.execute(
        "UPDATE clients SET name = ?, phone = ?, email = ? WHERE client_id = ?",
        (new_name, new_phone, new_email, client_id),
    )
    conn.commit()
    conn.close()
    print(f"Updated client_id={client_id}: name={new_name}, phone={new_phone}, email={new_email}")


def update_dog_name(dog_id, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE dogs SET dog_name = ? WHERE dog_id = ?", (new_name, dog_id))
    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()
    if rows_updated:
        print(f"Updated dog_id={dog_id} to '{new_name}'")
    else:
        print(f"No dog found with dog_id={dog_id}")


def adjust_balance(client_id, new_balance):
    """Manually override a client's balance to a specific number (for corrections)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clients SET balance_days = ? WHERE client_id = ?", (new_balance, client_id))
    conn.commit()
    conn.close()
    print(f"client_id={client_id} balance manually set to {new_balance} days")


def find_dog_by_name(dog_name):
    """
    Search for dogs matching a name (partial match, case-insensitive).
    Returns a list of (dog_id, dog_name, client_id, client_name) tuples.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT d.dog_id, d.dog_name, c.client_id, c.name
           FROM dogs d
           JOIN clients c ON d.client_id = c.client_id
           WHERE d.dog_name LIKE ?
           ORDER BY d.dog_name""",
        (f"%{dog_name}%",),
    )
    results = cursor.fetchall()
    conn.close()
    return results


def delete_client(client_id):
    """Deletes a client and everything tied to them: their dogs, check-in history, and purchase history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM clients WHERE client_id = ?", (client_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        print(f"No client found with client_id={client_id}")
        return False
    client_name = row[0]

    cursor.execute("DELETE FROM checkins WHERE client_id = ?", (client_id,))
    deleted_checkins = cursor.rowcount
    cursor.execute("DELETE FROM purchases WHERE client_id = ?", (client_id,))
    deleted_purchases = cursor.rowcount
    cursor.execute("DELETE FROM dogs WHERE client_id = ?", (client_id,))
    deleted_dogs = cursor.rowcount
    cursor.execute("DELETE FROM clients WHERE client_id = ?", (client_id,))

    conn.commit()
    conn.close()
    print(f"Deleted client '{client_name}': {deleted_dogs} dog(s), "
          f"{deleted_checkins} check-in(s), {deleted_purchases} purchase(s) removed.")
    return True


def delete_dog(dog_id):
    """Deletes a dog and any check-in history tied to it. Does not affect the client or their balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dog_name FROM dogs WHERE dog_id = ?", (dog_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        print(f"No dog found with dog_id={dog_id}")
        return False
    dog_name = row[0]
    cursor.execute("DELETE FROM checkins WHERE dog_id = ?", (dog_id,))
    deleted_checkins = cursor.rowcount
    cursor.execute("DELETE FROM dogs WHERE dog_id = ?", (dog_id,))
    conn.commit()
    conn.close()
    print(f"Deleted dog '{dog_name}' and {deleted_checkins} associated check-in(s).")
    return True


def list_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT client_id, name, balance_days FROM clients ORDER BY name")
    results = cursor.fetchall()
    conn.close()
    return results

def low_balance_clients(threshold=1.0):
    """Returns clients at or below the threshold (flags repurchase needed)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT client_id, name, balance_days FROM clients WHERE balance_days <= ?",
        (threshold,),
    )
    results = cursor.fetchall()
    conn.close()
    return results
