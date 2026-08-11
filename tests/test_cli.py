import sqlite3
import os
import pytest
import pexpect
from daycare import add_dog, check_in, get_unpaid_visits, get_balance, low_balance_clients, check_out_dog, delete_client

def test_add_client_successfully(spawn_app):
    child = spawn_app()
    
    # 1. Complete the UI workflow
    child.expect("1. Add new client")
    child.sendline("1")
    
    child.expect("Client name:")
    child.sendline("Jon Wolfe")
    
    child.expect(r"Phone \(optional\):")
    child.sendline("")  
    
    child.expect(r"Email \(optional\):")
    child.sendline("jon@example.com")
    
    # 2. Wait for the app to finish processing and return to the menu
    child.expect("1. Add new client")
    
    # 3. THE BACKEND ASSERTION: Directly query the isolated test database
    db_path = os.environ.get("DATABASE_PATH")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query for the specific client we just added
    cursor.execute("SELECT name, email FROM clients WHERE email = 'jon@example.com'")
    client_row = cursor.fetchone()
    conn.close()
    
    # 4. Verify the database state
    assert client_row is not None, "Client was not found in the database!"
    
    db_name, db_email = client_row
    assert db_name == "Jon Wolfe"
    assert db_email == "jon@example.com"

def test_add_dog_to_existing_client(spawn_app, existing_client):
     child = spawn_app()

     child.expect("2. Add dog to existing client")
     child.sendline("2")

     child.expect(r"Enter the number of the client \(or press Enter to cancel\):")
     child.sendline("1")

     child.expect("Dog's name:")
     child.sendline("Munchi")

     child.expect("1. Add new client")

     db_path = os.environ.get("DATABASE_PATH")

     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()

     cursor.execute("SELECT dog_name, client_id FROM dogs WHERE dog_name = 'Munchi' AND client_id = ?",  (existing_client,))
     dogs_row = cursor.fetchone()
     conn.close()
    
     assert dogs_row is not None, "Dog was not found in the database!"

     db_dog_name, db_client_id = dogs_row
     assert db_client_id == existing_client
     assert db_dog_name == "Munchi"

def test_no_input_add_client(spawn_app):
     child = spawn_app()

     child.expect("Choose an option:")
     child.sendline("1")

     child.expect("Client name:")
     child.sendline("")

     child.expect(r"Phone \(optional\)")
     child.sendline("")

     child.expect(r"Email \(optional\)")
     child.sendline("")

     child.expect("Choose an option:")
     
     db_path = os.environ.get("DATABASE_PATH")

     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()

     cursor.execute("SELECT name FROM clients WHERE name = ''")
     client_row = cursor.fetchone()
     conn.close()

     assert client_row is not None, "Client was not found in the database!"
    
     db_name, = client_row
     assert db_name == ""

def test_unpaid_daily_visits_total(existing_client):
     dog_id = add_dog(existing_client, "Munchi")
     check_in(existing_client, [dog_id], "daily", "2026-07-20")
     check_in(existing_client, [dog_id], "daily", "2026-07-21")
     result = get_unpaid_visits(existing_client, "2026-07-20", "2026-07-21")
     assert result["num_days"] == 2
     assert result["total_owed"] == 52.00

def test_get_balance_logs_daily_payments(existing_client):
     dog_id = add_dog(existing_client, "Munchi")
     check_in(existing_client, [dog_id], "daily", "2026-07-20")
     check_in(existing_client, [dog_id], "daily", "2026-07-21")
     assert get_balance(existing_client) == 0.00
# This test shows buggy behavior and points out the get_balance function 
# only ever queries balance_days and doesn't take checkins, payment_type 
# or paid into account at all

# Note: low_balance_clients() shares this same bug — it also only queries
# balance_days, so clients with unpaid daily charges won't appear there either.
     
def test_check_out_flow(existing_client):
     dog_id = add_dog(existing_client, "Munchi")
     check_in(existing_client, [dog_id], "daily", "2026-08-01")
     result = check_out_dog(dog_id, "2026-08-01")
     assert result["paid"] == 0.00
     assert result["client_id"] == existing_client
     
     db_path = os.environ.get("DATABASE_PATH")

     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()

     cursor.execute("SELECT checked_out FROM checkins WHERE dog_id = ? AND checkin_date = ?", (dog_id, "2026-08-01"))
     client_row = cursor.fetchone()
     conn.close()
     db_checked_out, = client_row
     assert db_checked_out == 1

def test_delete_client(existing_client):
     dog_id = add_dog(existing_client, "Munchi")
     check_in(existing_client, [dog_id], "daily", "2026-08-01")
     result = delete_client(existing_client)
     
     db_path = os.environ.get("DATABASE_PATH")

     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()

     cursor.execute("SELECT client_id FROM clients WHERE client_id = ?", (existing_client,)) 
     client_row = cursor.fetchone()
     assert client_row is None
