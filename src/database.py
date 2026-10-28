
from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_DIR / "data" / "property_quality.db"
REPORT_DIR = PROJECT_DIR / "reports"


def get_connection():
    """Open a connection to the project's SQLite database."""
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_FILE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables():
    """Create the property and issue tables if they do not exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS property_records (
                property_id TEXT,
                source_row INTEGER PRIMARY KEY,
                city TEXT,
                year_built INTEGER,
                construction_type TEXT,
                occupancy TEXT,
                insured_value_inr REAL,
                roof_type TEXT,
                quality_score REAL,
                quality_status TEXT,
                has_quality_issue INTEGER
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS data_quality_issues (
                issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT,
                source_row INTEGER,
                column_name TEXT,
                issue_type TEXT,
                severity TEXT,
                details TEXT,
                FOREIGN KEY (source_row)
                    REFERENCES property_records(source_row)
            )
            """
        )


def load_reports_into_database():
    """Load the latest pipeline reports into SQLite."""
    property_file = REPORT_DIR / "validated_properties.csv"
    issues_file = REPORT_DIR / "data_quality_issues.csv"

    if not property_file.exists() or not issues_file.exists():
        raise FileNotFoundError(
            "Pipeline reports not found. Run `python src/main.py` first."
        )

    properties = pd.read_csv(property_file)
    issues = pd.read_csv(issues_file)

    # Use source row numbers to distinguish duplicate property IDs.
    properties["source_row"] = range(2, len(properties) + 2)
    properties["has_quality_issue"] = (
        properties["has_quality_issue"].astype(int)
    )

    with get_connection() as connection:
        # Reload atomically so repeated runs do not duplicate records.
        connection.execute("DELETE FROM data_quality_issues")
        connection.execute("DELETE FROM property_records")

        properties.to_sql(
            "property_records",
            connection,
            if_exists="append",
            index=False,
        )

        issues = issues.rename(columns={"column": "column_name"})

        issues.to_sql(
            "data_quality_issues",
            connection,
            if_exists="append",
            index=False,
        )


def run_analysis_queries():
    """Run SQL summaries and export their results for Excel Online."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    queries = {
        "sql_issues_by_type.csv": """
            SELECT issue_type,
                   COUNT(*) AS issue_count
            FROM data_quality_issues
            GROUP BY issue_type
            ORDER BY issue_count DESC, issue_type
        """,
        "sql_issues_by_severity.csv": """
            SELECT severity,
                   COUNT(*) AS issue_count
            FROM data_quality_issues
            GROUP BY severity
            ORDER BY issue_count DESC
        """,
        "sql_quality_by_city.csv": """
            SELECT city,
                   COUNT(*) AS property_count,
                   ROUND(AVG(quality_score), 2) AS average_quality_score,
                   SUM(has_quality_issue) AS flagged_records
            FROM property_records
            GROUP BY city
            ORDER BY average_quality_score ASC, city
        """,
        "sql_low_quality_records.csv": """
            SELECT property_id,
                   source_row,
                   city,
                   quality_score,
                   quality_status
            FROM property_records
            WHERE has_quality_issue = 1
            ORDER BY quality_score ASC, property_id
        """,
    }

    with get_connection() as connection:
        for filename, query in queries.items():
            result = pd.read_sql_query(query, connection)
            result.to_csv(REPORT_DIR / filename, index=False)

        property_count = pd.read_sql_query(
            "SELECT COUNT(*) AS count FROM property_records",
            connection,
        ).iloc[0]["count"]

        issue_count = pd.read_sql_query(
            "SELECT COUNT(*) AS count FROM data_quality_issues",
            connection,
        ).iloc[0]["count"]

    print("\nSQL DATABASE ANALYSIS COMPLETE")
    print(f"Database: {DATABASE_FILE}")
    print(f"Properties loaded: {property_count}")
    print(f"Issues loaded: {issue_count}")
    print(f"SQL reports saved to: {REPORT_DIR}")


def main():
    create_tables()
    load_reports_into_database()
    run_analysis_queries()


if __name__ == "__main__":
    main()
