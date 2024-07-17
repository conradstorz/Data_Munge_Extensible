import pytest
import pandas as pd
from pathlib import Path
from process_float_outexcel import process, process_floatReport_csv
import tempfile
import json

@pytest.fixture
def sample_csv():
    return """Location,Reject Balance,Balance,Today's Float,Route
A,100,200,300,X
B,150,250,350,Y
C,200,300,400,Z"""

@pytest.fixture
def sample_json():
    return {
        "Balance": "float",
        "Reject Balance": "float",
        "Today's Float": "float"
    }

@pytest.fixture
def create_temp_csv(sample_csv):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp_csv:
        temp_csv.write(sample_csv)
        temp_csv.seek(0)
    yield temp_csv.name
    Path(temp_csv.name).unlink()

@pytest.fixture
def create_temp_json(sample_json):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_json:
        json.dump(sample_json, temp_json)
        temp_json.seek(0)
    yield temp_json.name
    Path(temp_json.name).unlink()

def test_process_floatReport_csv(create_temp_csv, create_temp_json):
    output_file_path = Path(tempfile.mktemp(suffix='.xlsx'))
    result = process_floatReport_csv(output_file_path, Path(create_temp_csv), '2024-01-01')
    assert result is not False
    df = result["Outputfile0.xlsx"]
    assert df.at[df.index[-2], "Location"] == "Report ran: 2024-01-01"
    assert df.at["Totals", "Location"] == "               Route Totals"
    assert "Route" not in df.columns
    assert df["Balance"].dtype == float
    assert df["Today's Float"].dtype == float
    assert df["Reject Balance"].dtype == float

def test_process(create_temp_csv):
    output_file_path = Path(tempfile.mktemp(suffix='.xlsx'))
    process(Path(create_temp_csv))
    # Add additional checks if needed for the process function output

if __name__ == "__main__":
    pytest.main()
