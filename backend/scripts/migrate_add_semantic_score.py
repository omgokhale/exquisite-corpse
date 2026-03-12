#!/usr/bin/env python3
"""
Migration script to add semantic_score column to segments table.
Run this once to update your existing database schema.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import DATA_DIR


def migrate():
    """Add semantic_score column to segments table"""
    db_path = DATA_DIR / "exquisite_corpse.db"

    print("=" * 60)
    print("Database Migration: Add semantic_score to segments")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(segments)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'semantic_score' in columns:
            print("\n✓ Column 'semantic_score' already exists. No migration needed.")
            return

        print("\n→ Adding 'semantic_score' column...")

        # Add the column with NULL default
        cursor.execute("""
            ALTER TABLE segments
            ADD COLUMN semantic_score REAL
        """)

        conn.commit()

        print("✓ Migration successful!")
        print("\nColumn added: semantic_score (REAL, nullable)")
        print("\nYou can now run: python scripts/compute_semantic_scores.py")

    except sqlite3.OperationalError as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
