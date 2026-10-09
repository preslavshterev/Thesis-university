import getpass

from auth import hash_password

if __name__ == "__main__":
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Repeat password: ")

    if not username or not password:
        raise SystemExit("Username and password must not be empty.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    print("\nAdd these two lines to the .env file:\n")
    print(f"DASHBOARD_USER={username}")
    print(f"DASHBOARD_PASSWORD_HASH={hash_password(password)}")