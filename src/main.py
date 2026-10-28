
from pathlib import Path

import pandas as pd


# --------------------------------------------------
#PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "data" / "sample_properties.csv"
REPORT_DIR = PROJECT_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Illustrative penalties for this project, not an industry standard.
PENALTIES = {
    "MISSING_REQUIRED_VALUE": 15,
    "DUPLICATE_PROPERTY_ID": 20,
    "INVALID_YEAR": 15,
    "INVALID_INSURED_VALUE": 20,
    "INVALID_NUMERIC_VALUE": 15,
    "UNKNOWN_CONSTRUCTION_TYPE": 5,
    "UNKNOWN_OCCUPANCY": 5,
    "UNKNOWN_ROOF_TYPE": 5,
}

ALLOWED_CONSTRUCTION_TYPES = {
    "Concrete", "Brick", "Steel", "Wood", "Other"
}

ALLOWED_OCCUPANCIES = {
    "Residential", "Commercial", "Industrial"
}

ALLOWED_ROOF_TYPES = {
    "Concrete", "Tile", "Metal", "Other"
}

REQUIRED_COLUMNS = [
    "property_id",
    "city",
    "year_built",
    "construction_type",
    "occupancy",
    "insured_value_inr",
    "roof_type",
]


# --------------------------------------------------
#ISSUE-REPORTING HELPER
# --------------------------------------------------

def add_issue(
    issues,
    df,
    row_index,
    column,
    issue_type,
    severity,
    details,
):
    """Add a data-quality issue for a source record."""
    property_id = df.loc[row_index, "property_id"]

    issues.append(
        {
            "property_id": property_id,
            "source_row": row_index + 2,
            "column": column,
            "issue_type": issue_type,
            "severity": severity,
            "details": details,
        }
    )


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------

def run_pipeline(input_file=None):
    """Load, validate, score, and report property data."""

    # Load source data without modifying the original CSV.
    input_path = Path(input_file) if input_file else INPUT_FILE
    df = pd.read_csv(input_path)

    expected_columns = {
        "property_id",
        "city",
        "year_built",
        "construction_type",
        "occupancy",
        "insured_value_inr",
        "roof_type",
    }

    missing_columns = expected_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Input file is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # Normalize text fields.
    text_columns = [
        "property_id",
        "city",
        "construction_type",
        "occupancy",
        "roof_type",
    ]

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

        # Treat whitespace-only text as missing.
        df[column] = df[column].replace("", pd.NA)

    # Preserve original numeric values before conversion.
    numeric_columns = ["year_built", "insured_value_inr"]

    raw_numeric_values = {
        column: df[column].copy()
        for column in numeric_columns
    }

    # Convert numbers safely. Invalid text becomes NaN,
    # but the original values remain available for diagnosis.
    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    issues = []

    # --------------------------------------------------
    #MISSING REQUIRED VALUES
    # --------------------------------------------------

    for index, row in df.iterrows():
        for column in REQUIRED_COLUMNS:
            value = row[column]

            if pd.isna(value):
                # Distinguish malformed numeric text from a blank.
                if column in raw_numeric_values:
                    original_value = raw_numeric_values[column].loc[index]

                    if (
                        pd.notna(original_value)
                        and str(original_value).strip() != ""
                    ):
                        # This value will receive an invalid-number
                        # issue instead of a missing-value issue.
                        continue

                add_issue(
                    issues,
                    df,
                    index,
                    column,
                    "MISSING_REQUIRED_VALUE",
                    "HIGH",
                    f"Required field '{column}' is missing or blank.",
                )

    # --------------------------------------------------
    #MALFORMED NUMERIC VALUES
    # --------------------------------------------------

    for column, original_values in raw_numeric_values.items():
        for index, original_value in original_values.items():
            if pd.isna(original_value):
                continue

            if str(original_value).strip() == "":
                continue

            if pd.isna(df.loc[index, column]):
                add_issue(
                    issues,
                    df,
                    index,
                    column,
                    "INVALID_NUMERIC_VALUE",
                    "HIGH",
                    f"Value '{original_value}' is not a valid number.",
                )

    # --------------------------------------------------
    # DUPLICATE PROPERTY IDS
    # --------------------------------------------------

    duplicate_mask = (
        df["property_id"].notna()
        & df["property_id"].duplicated(keep=False)
    )

    for index in df.index[duplicate_mask]:
        add_issue(
            issues,
            df,
            index,
            "property_id",
            "DUPLICATE_PROPERTY_ID",
            "HIGH",
            "This property ID appears more than once in the input file.",
        )

    # --------------------------------------------------
    # VALIDATE YEAR BUILT
    # --------------------------------------------------

    current_year = pd.Timestamp.today().year

    for index, year in df["year_built"].items():
        if pd.notna(year) and not (1800 <= year <= current_year):
            add_issue(
                issues,
                df,
                index,
                "year_built",
                "INVALID_YEAR",
                "HIGH",
                f"Year must be between 1800 and {current_year}.",
            )

    # --------------------------------------------------
    # VALIDATE INSURED VALUE
    # --------------------------------------------------

    for index, value in df["insured_value_inr"].items():
        if pd.notna(value) and value <= 0:
            add_issue(
                issues,
                df,
                index,
                "insured_value_inr",
                "INVALID_INSURED_VALUE",
                "HIGH",
                "Insured value must be greater than zero.",
            )

    # --------------------------------------------------
    # VALIDATE CATEGORIES
    # --------------------------------------------------

    category_rules = {
        "construction_type": (
            ALLOWED_CONSTRUCTION_TYPES,
            "UNKNOWN_CONSTRUCTION_TYPE",
        ),
        "occupancy": (
            ALLOWED_OCCUPANCIES,
            "UNKNOWN_OCCUPANCY",
        ),
        "roof_type": (
            ALLOWED_ROOF_TYPES,
            "UNKNOWN_ROOF_TYPE",
        ),
    }

    for column, (allowed_values, issue_type) in category_rules.items():
        for index, value in df[column].items():
            # Missing values are handled by the required-field checks.
            if pd.isna(value):
                continue

            if value not in allowed_values:
                add_issue(
                    issues,
                    df,
                    index,
                    column,
                    issue_type,
                    "MEDIUM",
                    f"Unexpected {column} category: {value}.",
                )

    # --------------------------------------------------
    # BUILD ISSUE REPORT
    # --------------------------------------------------

    issue_columns = [
        "property_id",
        "source_row",
        "column",
        "issue_type",
        "severity",
        "details",
    ]

    issues_df = pd.DataFrame(
        issues,
        columns=issue_columns,
    )

    # --------------------------------------------------
    # CALCULATE RECORD-LEVEL SCORES
    # --------------------------------------------------

    row_penalties = {
        index: 0
        for index in df.index
    }

    for issue in issues:
        source_index = issue["source_row"] - 2
        penalty = PENALTIES[issue["issue_type"]]

        row_penalties[source_index] += penalty

    df["quality_score"] = [
        max(0, 100 - row_penalties[index])
        for index in df.index
    ]

    df["has_quality_issue"] = df["quality_score"] < 100

    def quality_status(score):
        if score >= 90:
            return "Good"
        if score >= 70:
            return "Needs Review"
        return "Poor"

    df["quality_status"] = df["quality_score"].map(quality_status)


    # EXPORT DETAILED REPORTS
    

    df.to_csv(
        REPORT_DIR / "validated_properties.csv",
        index=False,
    )

    issues_df.to_csv(
        REPORT_DIR / "data_quality_issues.csv",
        index=False,
    )

    score_columns = [
        "property_id",
        "city",
        "quality_score",
        "quality_status",
        "has_quality_issue",
    ]

    df[score_columns].to_csv(
        REPORT_DIR / "property_quality_scores.csv",
        index=False,
    )

    # PORTFOLIO SUMMARY
    

    high_severity_count = (
        int((issues_df["severity"] == "HIGH").sum())
        if not issues_df.empty
        else 0
    )

    medium_severity_count = (
        int((issues_df["severity"] == "MEDIUM").sum())
        if not issues_df.empty
        else 0
    )

    summary = pd.DataFrame(
        [
            {
                "metric": "Total property records",
                "value": len(df),
            },
            {
                "metric": "Records with at least one issue",
                "value": int(df["has_quality_issue"].sum()),
            },
            {
                "metric": "Total issues detected",
                "value": len(issues_df),
            },
            {
                "metric": "Average quality score",
                "value": round(df["quality_score"].mean(), 2),
            },
            {
                "metric": "High-severity issues",
                "value": high_severity_count,
            },
            {
                "metric": "Medium-severity issues",
                "value": medium_severity_count,
            },
        ]
    )

    summary.to_csv(
        REPORT_DIR / "quality_summary.csv",
        index=False,
    )

    
    #QUALITY-STATUS DISTRIBUTION
    

    status_summary = (
        df["quality_status"]
        .value_counts()
        .rename_axis("quality_status")
        .reset_index(name="record_count")
    )

    status_summary.to_csv(
        REPORT_DIR / "quality_status_distribution.csv",
        index=False,
    )

    
    #EXECUTION SUMMARY

    print("\nPROPERTY DATA QUALITY CHECK COMPLETE")
    print(f"Records processed: {len(df)}")
    print(
        "Records with issues: "
        f"{int(df['has_quality_issue'].sum())}"
    )
    print(f"Total issues detected: {len(issues_df)}")
    print(
        "Average quality score: "
        f"{df['quality_score'].mean():.2f}"
    )
    print(f"Reports saved to: {REPORT_DIR}")


if __name__ == "__main__":
    run_pipeline()


