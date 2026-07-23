"""
Daycare Tracker - Interactive Menu
Run this file each day to add clients, check dogs in, and check balances.

Usage: python3 app.py
"""
import sys
import io

# Prevent crashes on Windows consoles that can't display certain characters (e.g. emoji)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from daycare import (
    add_client, add_dog, purchase_pack, check_in, get_balance,
    get_client_dogs, whos_here_today, low_balance_clients,
    get_unpaid_visits, list_clients,
    update_client, update_dog_name, adjust_balance, find_dog_by_name,
    whos_still_here, check_out_dog, mark_single_checkin_paid, mark_all_unpaid_paid, check_out_all,
    delete_dog, delete_client,
)


def get_int(prompt):
    """Prompts for an integer. Returns None if left blank (so callers can treat it as 'cancel')."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("That's not a valid number. Try again, or press Enter with nothing to cancel.")


def get_float(prompt):
    """Prompts for a number (decimals allowed). Returns None if left blank."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            print("That's not a valid number. Try again, or press Enter with nothing to cancel.")


def select_dogs_numbered(dogs, prompt, allow_multiple=False):
    """
    Shows a numbered list of (dog_id, dog_name) pairs and lets the user pick by number.
    Returns a list of dog_ids (single-item list if allow_multiple=False).
    Returns [] if cancelled.
    """
    for idx, (did, dname) in enumerate(dogs, start=1):
        print(f"  {idx}. {dname}")

    if not allow_multiple:
        num = get_int(prompt)
        if num is None or num < 1 or num > len(dogs):
            return []
        return [dogs[num - 1][0]]

    raw = input(prompt).strip()
    if raw == "":
        return []
    dog_ids = []
    for piece in raw.split(","):
        piece = piece.strip()
        if piece.isdigit() and 1 <= int(piece) <= len(dogs):
            dog_ids.append(dogs[int(piece) - 1][0])
        elif piece:
            print(f"Skipping invalid entry: '{piece}'")
    return dog_ids


def menu():
    print("\n" + "=" * 40)
    print("DAYCARE TRACKER")
    print("=" * 40)
    print("1. Add new client")
    print("2. Add dog to existing client")
    print("3. Check in dog(s)")
    print("4. Purchase a prepay pack")
    print("5. View client's balance")
    print("6. View who's checked in today")
    print("7. View low/negative balance clients")
    print("8. View unpaid visits for a client")
    print("9. Check a dog out")
    print("9b. Check out ALL dogs for a day")
    print("10. List all clients")
    print("11. Edit client info (name/phone/email)")
    print("12. Edit a dog's name")
    print("13. Manually correct a client's balance")
    print("14. Delete a dog (e.g. fix a duplicate entry)")
    print("15. Delete a client (removes all their dogs and history too)")
    print("0. Exit")
    return input("Choose an option: ").strip()


def pick_client():
    clients = list_clients()
    if not clients:
        print("No clients yet.")
        return None
    for idx, (cid, name, balance) in enumerate(clients, start=1):
        print(f"  {idx}. {name} (balance: {balance} days)")
    num = get_int("Enter the number of the client (or press Enter to cancel): ")
    if num is None or num < 1 or num > len(clients):
        return None
    return clients[num - 1][0]


def main():
    while True:
        try:
            choice = menu()
            result = run_choice(choice)
            if result == "exit":
                break
        except Exception as e:
            print(f"\nSomething went wrong, but the program is still running: {e}")
            print("Try that menu option again.")


def run_choice(choice):
        if choice == "1":
            name = input("Client name: ").strip()
            phone = input("Phone (optional): ").strip()
            email = input("Email (optional): ").strip()
            add_client(name, phone, email)

        elif choice == "2":
            client_id = pick_client()
            if client_id:
                dog_name = input("Dog's name: ").strip()
                add_dog(client_id, dog_name)

        elif choice == "3":
            search = input("Type part or all of the dog's name: ").strip()
            matches = find_dog_by_name(search)
            if not matches:
                print("No dogs found matching that name.")
            else:
                # matches: list of (dog_id, dog_name, client_id, client_name)
                if len(matches) == 1:
                    dog_id, dog_name, client_id, client_name = matches[0]
                else:
                    print("Multiple matches found:")
                    for idx, (did, dname, cid, cname) in enumerate(matches, start=1):
                        print(f"  {idx}. {dname} (owner: {cname})")
                    num = get_int("Enter the number of the dog checking in (or press Enter to cancel): ")
                    if num is None or num < 1 or num > len(matches):
                        print("Cancelled.")
                        return
                    dog_id, dog_name, client_id, client_name = matches[num - 1]

                print(f"Owner: {client_name}")
                owner_dogs = get_client_dogs(client_id)
                if len(owner_dogs) > 1:
                    print(f"{client_name} also has other dog(s) on file. Select ALL dogs checking in today:")
                    dog_ids = select_dogs_numbered(
                        owner_dogs,
                        "Enter number(s), comma-separated (or press Enter for just the one found): ",
                        allow_multiple=True,
                    )
                    if not dog_ids:
                        dog_ids = [dog_id]
                else:
                    dog_ids = [dog_id]

                ptype = input("Payment type (prepay/daily): ").strip().lower()
                check_in(client_id, dog_ids, ptype)

        elif choice == "4":
            client_id = pick_client()
            if client_id:
                dog_count = get_int("Package for how many dogs (1 or 2), or Enter to cancel: ")
                if dog_count is None:
                    print("Cancelled.")
                else:
                    days = get_int("Package size (5, 10, or 20), or Enter to cancel: ")
                    if days is None:
                        print("Cancelled.")
                    else:
                        try:
                            purchase_pack(client_id, dog_count, days)
                        except ValueError as e:
                            print(f"Error: {e}")

        elif choice == "5":
            client_id = pick_client()
            if client_id:
                print(f"Balance: {get_balance(client_id)} days")

        elif choice == "6":
            date_input = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
            results = whos_here_today(date_input if date_input else None)
            if not results:
                print("No check-ins found for that date.")
            for name, dog, ptype, paid, amount in results:
                paid_str = "paid" if paid else "UNPAID"
                print(f"  {name} - {dog} - {ptype} - {paid_str} - ${amount:.2f}")

        elif choice == "7":
            results = low_balance_clients(threshold=1.0)
            if not results:
                print("No clients at or below threshold.")
            for idx, (cid, name, balance) in enumerate(results, start=1):
                flag = " - NEGATIVE" if balance < 0 else ""
                print(f"  {idx}. {name}: {balance} days{flag}")

        elif choice == "8":
            client_id = pick_client()
            if client_id:
                start = input("Start date (YYYY-MM-DD): ").strip()
                end = input("End date (YYYY-MM-DD): ").strip()
                get_unpaid_visits(client_id, start, end)

        elif choice == "9":
            date_input = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
            target_date = date_input if date_input else None
            still_here = whos_still_here(target_date)
            if not still_here:
                print("No dogs currently checked in for that date.")
            else:
                print("Currently checked in:")
                for idx, (checkin_id, dog_id, dog_name, client_id, client_name, ptype, paid, amount) in enumerate(still_here, start=1):
                    paid_str = "" if ptype == "prepay" else (" - PAID" if paid else " - UNPAID")
                    print(f"  {idx}. {dog_name} (owner: {client_name}){paid_str}")
                num = get_int("Enter the number of the dog to check out (or press Enter to cancel): ")
                if num is None or num < 1 or num > len(still_here):
                    print("Cancelled.")
                else:
                    picked_client_id = still_here[num - 1][3]
                    picked_client_name = still_here[num - 1][4]

                    # Find every dog belonging to the same client still checked in that day (siblings)
                    siblings = [entry for entry in still_here if entry[3] == picked_client_id]

                    if len(siblings) > 1:
                        print(f"{picked_client_name} has {len(siblings)} dogs checked in today - checking out all of them together.")

                    results = []
                    for checkin_id, dog_id, dog_name, client_id, client_name, ptype, paid, amount in siblings:
                        result = check_out_dog(dog_id, target_date)
                        if result:
                            results.append(result)

                    unpaid_daily_results = [r for r in results if r["payment_type"] == "daily" and not r["paid"]]
                    if unpaid_daily_results:
                        print("This was an unpaid daily visit.")
                        print("  1. Mark as paid")
                        print("  2. Mark ALL unpaid visits for this client as paid")
                        print("  3. Leave unpaid for now")
                        pay_choice = input("Choose an option: ").strip()
                        if pay_choice == "1":
                            for r in unpaid_daily_results:
                                mark_single_checkin_paid(r["checkin_id"])
                        elif pay_choice == "2":
                            mark_all_unpaid_paid(picked_client_id)

        elif choice == "9b":
            date_input = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
            target_date = date_input if date_input else None
            unpaid_daily = check_out_all(target_date)
            if unpaid_daily:
                print(f"\n{len(unpaid_daily)} unpaid daily-rate visit(s) among those checked out:")
                for entry in unpaid_daily:
                    print(f"  {entry['dog_name']} (owner: {entry['client_name']}) - ${entry['amount']:.2f}")
                print("\nFor each one, mark as paid now or leave unpaid.")
                for entry in unpaid_daily:
                    ans = input(f"  {entry['dog_name']} ({entry['client_name']}) - paid? (y/n): ").strip().lower()
                    if ans == "y":
                        mark_single_checkin_paid(entry["checkin_id"])
            print("\nDone checking out everyone.")

        elif choice == "10":
            for idx, (cid, name, balance) in enumerate(list_clients(), start=1):
                print(f"  {idx}. {name} - {balance} days")

        elif choice == "11":
            client_id = pick_client()
            if client_id:
                print("Leave any field blank to keep it unchanged.")
                name = input("New name: ").strip()
                phone = input("New phone: ").strip()
                email = input("New email: ").strip()
                update_client(client_id, name or None, phone or None, email or None)

        elif choice == "12":
            client_id = pick_client()
            if client_id:
                dogs = get_client_dogs(client_id)
                if not dogs:
                    print("This client has no dogs on file.")
                else:
                    dog_ids = select_dogs_numbered(dogs, "Enter the number of the dog to rename (or press Enter to cancel): ")
                    if not dog_ids:
                        print("Cancelled.")
                    else:
                        new_name = input("New dog name: ").strip()
                        update_dog_name(dog_ids[0], new_name)

        elif choice == "13":
            client_id = pick_client()
            if client_id:
                new_balance = get_float("Enter correct balance in days (or press Enter to cancel): ")
                if new_balance is None:
                    print("Cancelled.")
                else:
                    adjust_balance(client_id, new_balance)

        elif choice == "14":
            client_id = pick_client()
            if client_id:
                dogs = get_client_dogs(client_id)
                if not dogs:
                    print("This client has no dogs on file.")
                else:
                    dog_ids = select_dogs_numbered(dogs, "Enter the number of the dog to delete (or press Enter to cancel): ")
                    if not dog_ids:
                        print("Cancelled.")
                    else:
                        dog_id = dog_ids[0]
                        dog_name = next(name for did, name in dogs if did == dog_id)
                        confirm = input(f"Are you sure you want to delete '{dog_name}'? This also removes their check-in history. (y/n): ").strip().lower()
                        if confirm == "y":
                            delete_dog(dog_id)
                        else:
                            print("Cancelled.")

        elif choice == "15":
            client_id = pick_client()
            if client_id:
                dogs = get_client_dogs(client_id)
                dog_names = ", ".join(name for did, name in dogs) if dogs else "no dogs on file"
                print(f"This client has: {dog_names}")
                print("Deleting this client removes them, all their dogs, and all check-in/purchase history.")
                confirm = input("Type DELETE (all caps) to confirm, or anything else to cancel: ").strip()
                if confirm == "DELETE":
                    delete_client(client_id)
                else:
                    print("Cancelled.")

        elif choice == "0":
            print("Goodbye!")
            return "exit"

        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
