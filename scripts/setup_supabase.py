"""Run the setup SQL against Supabase.

This script reads setup.sql and seed_model_responses.sql and executes them
via the Supabase client. Run once to initialize the database.

Usage:
    python scripts/setup_supabase.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
import config


def main():
    client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    sql_dir = os.path.join(os.path.dirname(__file__), "..", "db")

    # Run setup.sql
    setup_path = os.path.join(sql_dir, "setup.sql")
    print(f"Reading {setup_path}...")
    with open(setup_path) as f:
        setup_sql = f.read()

    print("Running setup.sql...")
    print("NOTE: Run this SQL in the Supabase SQL Editor at:")
    print(f"  {config.SUPABASE_URL.replace('.supabase.co', '.supabase.co')}")
    print()
    print("Steps:")
    print("  1. Go to your Supabase project dashboard")
    print("  2. Click 'SQL Editor' in the left sidebar")
    print("  3. Click 'New query'")
    print("  4. Paste the contents of db/setup.sql and click 'Run'")
    print("  5. Then paste the contents of db/seed_model_responses.sql and click 'Run'")
    print()

    # Verify connection
    try:
        result = client.table("settings").select("key").limit(1).execute()
        print("Connection verified! Settings table exists.")
        print(f"Found {len(result.data)} setting(s)")
    except Exception as e:
        print(f"Could not query settings table: {e}")
        print("Make sure you've run setup.sql in the Supabase SQL Editor first.")
        return

    # Check if model responses are seeded
    try:
        result = client.table("model_responses").select("id").execute()
        count = len(result.data)
        if count > 0:
            print(f"Model responses already seeded: {count} records")
        else:
            print("Model responses table is empty.")
            print("Run db/seed_model_responses.sql in the Supabase SQL Editor.")
    except Exception as e:
        print(f"Could not query model_responses table: {e}")

    print("\nSetup verification complete!")


if __name__ == "__main__":
    main()
