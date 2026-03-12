#!/usr/bin/env python3
"""
Migration script to add alignment_features column to segments table.
Run this once to update your existing database schema.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import DATA_DIR


def migrate():
    """Add alignment_features column to segments table"""
    db_path = DATA_DIR / "exquisite_corpse.db"

    print("=" * 60)
    print("Database Migration: Add alignment_features to segments")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(segments)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'alignment_features' in columns:
            print("\n✓ Column 'alignment_features' already exists. No migration needed.")
            return

        print("\n→ Adding 'alignment_features' column...")

        # Add the column with NULL default
        cursor.execute("""
            ALTER TABLE segments
            ADD COLUMN alignment_features TEXT
        """)

        conn.commit()

        print("✓ Migration successful!")
        print("\nColumn added: alignment_features (JSON/TEXT, nullable)")
        print("\nYou can now run: python3 scripts/compute_alignment_features.py")

    except sqlite3.OperationalError as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
