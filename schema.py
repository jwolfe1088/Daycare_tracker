"""
Database schema for Cheryl's Doggie Daycare tracker.
Run this once to create the database and tables.
"""
import sqlite3

DB_NAME = "daycare.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            balance_days REAL DEFAULT 0.0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dogs (
            dog_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            dog_name TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (client_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dog_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            payment_type TEXT NOT NULL,
            days_deducted REAL DEFAULT 0.0,
            amount_charged REAL DEFAULT 0.0,
            paid INTEGER DEFAULT 0,
            FOREIGN KEY (dog_id) REFERENCES dogs (dog_id),
            FOREIGN KEY (client_id) REFERENCES clients (client_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            purchase_date TEXT NOT NULL,
            dog_count INTEGER NOT NULL,
            days INTEGER NOT NULL,
            price_paid REAL NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (client_id)
        )
    """)

    conn.commit()
    conn.close()
    migrate_existing_database()
    print(f"Database '{DB_NAME}' created with tables: clients, dogs, checkins, purchases")


def migrate_existing_database():
    """Safely adds new columns to an existing database without touching any existing data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(checkins)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if "checked_out" not in existing_columns:
        cursor.execute("ALTER TABLE checkins ADD COLUMN checked_out INTEGER DEFAULT 0")
        conn.commit()
        print("Migrated database: added 'checked_out' tracking to checkins table.")
    conn.close()


if __name__ == "__main__":
    create_database()
