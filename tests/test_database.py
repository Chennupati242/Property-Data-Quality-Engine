
import sqlite3
import subprocess
import sys
from pathlib import Path

from src.database import (
    DATABASE_FILE,
    create_tables,
    load_reports_into_database,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent


def refresh_database():
    """Regenerate reports from the original sample dataset and reload SQLite."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "src" / "main.py")],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    create_tables()
    load_reports_into_database()


def test_database_file_exists():
    refresh_database()
    assert DATABASE_FILE.exists()


def test_database_contains_ten_properties():
    refresh_database()

    with sqlite3.connect(DATABASE_FILE) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM property_records"
        ).fetchone()[0]

    assert count == 10


def test_database_contains_seven_issues():
    refresh_database()

    with sqlite3.connect(DATABASE_FILE) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM data_quality_issues"
        ).fetchone()[0]

    assert count == 7


def test_sql_finds_duplicate_property_ids():
    refresh_database()

    with sqlite3.connect(DATABASE_FILE) as connection:
        rows = connection.execute(
            """
            SELECT property_id, COUNT(*) AS record_count
            FROM property_records
            GROUP BY property_id
            HAVING COUNT(*) > 1
            """
        ).fetchall()

    assert ("P005", 2) in rows


def test_loading_database_twice_does_not_duplicate_records():
    refresh_database()
    load_reports_into_database()

    with sqlite3.connect(DATABASE_FILE) as connection:
        property_count = connection.execute(
            "SELECT COUNT(*) FROM property_records"
        ).fetchone()[0]

        issue_count = connection.execute(
            "SELECT COUNT(*) FROM data_quality_issues"
        ).fetchone()[0]

    assert property_count == 10
    assert issue_count == 7

