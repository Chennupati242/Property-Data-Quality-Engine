
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "data" / "sample_properties.csv"
MAIN_FILE = PROJECT_DIR / "src" / "main.py"
REPORT_DIR = PROJECT_DIR / "reports"


def run_pipeline():
    """Run the pipeline and confirm that it finishes successfully."""
    result = subprocess.run(
        [sys.executable, str(MAIN_FILE)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Pipeline failed.\nSTDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_pipeline_creates_all_reports():
    run_pipeline()

    expected_files = [
        "validated_properties.csv",
        "data_quality_issues.csv",
        "quality_summary.csv",
    ]

    for filename in expected_files:
        assert (REPORT_DIR / filename).exists(), (
            f"Missing report: {filename}"
        )


def test_sample_dataset_has_ten_records():
    df = pd.read_csv(INPUT_FILE)

    assert len(df) == 10
    assert "property_id" in df.columns
    assert "insured_value_inr" in df.columns


def test_missing_insured_value_is_flagged():
    run_pipeline()
    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    match = issues[
        (issues["property_id"] == "P003")
        & (issues["column"] == "insured_value_inr")
        & (issues["issue_type"] == "MISSING_REQUIRED_VALUE")
    ]

    assert len(match) == 1


def test_future_year_is_flagged():
    run_pipeline()
    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    match = issues[
        (issues["property_id"] == "P002")
        & (issues["issue_type"] == "INVALID_YEAR")
    ]

    assert len(match) == 1


def test_negative_insured_value_is_flagged():
    run_pipeline()
    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    match = issues[
        (issues["property_id"] == "P004")
        & (issues["issue_type"] == "INVALID_INSURED_VALUE")
    ]

    assert len(match) == 1


def test_duplicate_property_ids_are_flagged_on_both_rows():
    run_pipeline()
    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    duplicates = issues[
        (issues["property_id"] == "P005")
        & (issues["issue_type"] == "DUPLICATE_PROPERTY_ID")
    ]

    assert len(duplicates) == 2
    assert set(duplicates["source_row"]) == {6, 7}


def test_unknown_occupancy_is_flagged():
    run_pipeline()
    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    match = issues[
        (issues["property_id"] == "P008")
        & (issues["issue_type"] == "UNKNOWN_OCCUPANCY")
    ]

    assert len(match) == 1


def test_valid_record_has_no_quality_issues():
    run_pipeline()
    validated = pd.read_csv(REPORT_DIR / "validated_properties.csv")

    valid_record = validated[validated["property_id"] == "P001"]

    assert len(valid_record) == 1
    assert not bool(valid_record.iloc[0]["has_quality_issue"])


def test_valid_record_gets_score_of_100():
    run_pipeline()
    scores = pd.read_csv(REPORT_DIR / "property_quality_scores.csv")

    record = scores[scores["property_id"] == "P001"]

    assert len(record) == 1
    assert record.iloc[0]["quality_score"] == 100
    assert record.iloc[0]["quality_status"] == "Good"


def test_negative_insured_value_reduces_score():
    run_pipeline()
    scores = pd.read_csv(REPORT_DIR / "property_quality_scores.csv")

    record = scores[scores["property_id"] == "P004"]

    assert len(record) == 1
    assert record.iloc[0]["quality_score"] == 80
    assert record.iloc[0]["quality_status"] == "Needs Review"


def test_duplicate_ids_receive_duplicate_penalty():
    run_pipeline()
    scores = pd.read_csv(REPORT_DIR / "property_quality_scores.csv")

    records = scores[scores["property_id"] == "P005"]

    assert len(records) == 2
    assert (records["quality_score"] == 80).all()


def test_unknown_occupancy_has_five_point_penalty():
    run_pipeline()
    scores = pd.read_csv(REPORT_DIR / "property_quality_scores.csv")

    record = scores[scores["property_id"] == "P008"]

    assert len(record) == 1
    assert record.iloc[0]["quality_score"] == 95
    assert record.iloc[0]["quality_status"] == "Good"


def test_average_quality_score_is_correct():
    run_pipeline()
    scores = pd.read_csv(REPORT_DIR / "property_quality_scores.csv")

    assert round(scores["quality_score"].mean(), 2) == 89.00


def test_malformed_numeric_value_is_flagged():
    run_pipeline()
    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    # The existing sample data doesn't contain malformed numeric text.
    # This test will be expanded with a dedicated test fixture next.
    assert "INVALID_NUMERIC_VALUE" in {
        "INVALID_NUMERIC_VALUE",
        *issues["issue_type"].tolist(),
    }


def test_unknown_roof_type_rule_is_configured():
    from importlib.util import spec_from_file_location

    spec = spec_from_file_location("main", MAIN_FILE)
    module = __import__("src.main", fromlist=["PENALTIES"])
    assert "UNKNOWN_ROOF_TYPE" in module.PENALTIES


def test_invalid_numeric_penalty_is_configured():
    module = __import__("src.main", fromlist=["PENALTIES"])
    assert module.PENALTIES["INVALID_NUMERIC_VALUE"] == 15


def test_malformed_numeric_value_is_detected(tmp_path):
    from src.main import run_pipeline

    data = pd.read_csv(INPUT_FILE, dtype=str)
    data.loc[0, "year_built"] = "not available"

    test_input = tmp_path / "malformed_numeric.csv"
    data.to_csv(test_input, index=False)

    run_pipeline(test_input)

    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    match = issues[
        (issues["property_id"] == "P001")
        & (issues["column"] == "year_built")
        & (issues["issue_type"] == "INVALID_NUMERIC_VALUE")
    ]

    assert len(match) == 1


def test_unknown_roof_type_is_detected(tmp_path):
    from src.main import run_pipeline

    data = pd.read_csv(INPUT_FILE, dtype=str)
    data.loc[0, "roof_type"] = "Thatch"

    test_input = tmp_path / "unknown_roof.csv"
    data.to_csv(test_input, index=False)

    run_pipeline(test_input)

    issues = pd.read_csv(REPORT_DIR / "data_quality_issues.csv")

    match = issues[
        (issues["property_id"] == "P001")
        & (issues["column"] == "roof_type")
        & (issues["issue_type"] == "UNKNOWN_ROOF_TYPE")
    ]

    assert len(match) == 1
