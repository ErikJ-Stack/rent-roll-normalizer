"""
Generate a SHA-256 hash for a Streamlit auth password.

Run locally (PowerShell):
    python tools/hash_password.py

Paste the hex digest into Streamlit Cloud → app → Settings → Secrets, under
the `[auth.users]` table. Example:

    [auth.users]
    alice = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
    bob   = "ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f"
"""

from __future__ import annotations

import getpass
import hashlib


def main() -> None:
    username = input("Username (label only — not hashed): ").strip()
    pw1 = getpass.getpass("Password: ")
    pw2 = getpass.getpass("Confirm password: ")
    if pw1 != pw2:
        print("Passwords do not match.")
        raise SystemExit(1)
    if not pw1:
        print("Password is empty.")
        raise SystemExit(1)

    digest = hashlib.sha256(pw1.encode("utf-8")).hexdigest()
    print()
    print("Paste this line into the [auth.users] table in Streamlit Cloud Secrets:")
    print()
    print(f'    {username or "USERNAME"} = "{digest}"')
    print()


if __name__ == "__main__":
    main()
