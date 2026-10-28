
# Property Data Quality & Enrichment Engine

A Python and SQL project that validates synthetic property-exposure
records, identifies data-quality issues, calculates record-level
quality scores, and generates reports for analytical review.

## 1. Business Problem

Property exposure datasets can contain missing fields, duplicate
identifiers, invalid values, and inconsistent classifications.
These issues can reduce the reliability of downstream analytics.

This project demonstrates a reproducible workflow for identifying
and reporting common data-quality problems before data is used in
further analysis.

**Important:** The included dataset is synthetic. This project is
an educational data-quality prototype, not a production insurance
system or a calibrated catastrophe-risk model.

## 2. Objectives

- Validate required property attributes.
- Detect duplicate property identifiers.
- Check year-built and insured-value fields.
- Identify unexpected occupancy and roof-type categories.
- Calculate configurable record-level quality scores.
- Store property records and issue results in SQLite.
- Generate CSV reports for analysis and visualization.
- Test validation rules and database behavior.

## 3. Technology Stack

- Python
- pandas
- SQLite and SQL
- pytest
- CSV reporting
- Excel Online for dashboard visualization

## 4. Project Structure

```text
property-data-quality-engine/
├── data/
│   ├── sample_properties.csv
│   └── property_quality.db
├── reports/
├── src/
│   ├── main.py
│   └── database.py
├── tests/
│   ├── test_data_quality.py
│   └── test_database.py
├── requirements.txt
├── README.md
└── run_project.py
```

The SQLite database and report files are generated outputs.
The exact files present in `reports/` may change as the pipeline runs.

## 5. How It Works

1. Load the property dataset from CSV.
2. Validate required fields and configured value rules.
3. Record detected issues with their type, severity, and details.
4. Calculate record-level quality scores.
5. Export validation and summary reports.
6. Load the property data and issue results into SQLite.
7. Execute SQL analysis and export SQL reports.
8. Run automated tests to check expected behavior.

## 6. Data-Quality Checks

The current implementation includes checks such as:

- Missing required values
- Duplicate property identifiers
- Invalid year-built values
- Invalid or non-positive insured values
- Unexpected occupancy categories
- Unexpected roof-type categories
- Malformed numeric values

The implemented rules and accepted categories are defined in
the project source code. They are configurable assumptions and
should be reviewed before applying the approach to other datasets.

## 7. Quality Scoring

The pipeline calculates record-level scores on a 0–100 scale
using configured penalties for detected issues.

The score is a project-defined data-quality indicator. It is not
an insurance risk score, predicted loss, or measure of catastrophe
risk. The exact penalty weights should be documented alongside
the implemented scoring rules.

## 8. Installation

Python 3 and a virtual environment are recommended.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Install pytest if it is not already included:

```bash
python -m pip install pytest
```

## 9. Run the Project

Run the complete pipeline:

```bash
python run_project.py
```

Alternatively, run each stage individually:

```bash
python src/main.py
python src/database.py
```

## 10. Run Tests

```bash
python -m pytest -v
```

Tests cover validation behavior, score calculations, report
generation, database contents, duplicate detection, and repeated
database loading.

## 11. Example Run

The sample run processed 10 synthetic property records and
detected 7 data-quality issues. The reported average quality
score was 89/100.

These values describe the included sample data only. They are
not performance benchmarks or results from a real insurer.

## 12. Reports and Dashboard

The pipeline produces CSV outputs for issue details, quality
scores, quality summaries, and SQL-based analysis.

The outputs can be opened in Excel Online to create charts and
a dashboard showing issue types, severity, quality scores, and
city-level comparisons.

## 13. Limitations and Future Improvements

- The dataset is synthetic and small.
- Validation rules and category lists are illustrative.
- Quality scores depend on configurable penalty weights.
- No real insurance claims, hazard observations, or insured
  property portfolios are used.
- The prototype is not a calibrated underwriting or catastrophe
  model.

Potential next improvements include larger test datasets,
configurable rule definitions, data profiling, structured logging,
automated report validation, and a reproducible dashboard workflow.

## 14. Author

Developed as a portfolio project demonstrating Python data
processing, SQL analytics, data validation, automated testing,
and reporting.
