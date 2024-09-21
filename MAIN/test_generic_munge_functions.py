import pytest
from pathlib import Path
from datetime import datetime
from generic_munge_functions import (
    print_pdf_using_os_subprocess,
    archive_original_file,
    is_date_valid,
    extract_dates,
    extract_date_from_filename,
)

# Mock the external module used in archive_original_file
class MockPLFH:
    @staticmethod
    def move_file_with_check(input_filename, outfile, exist_ok):
        return True

@pytest.fixture(autouse=True)
def mock_plfh(monkeypatch):
    # Replace the actual `plfh` module with the mock class in the test environment
    monkeypatch.setattr("generic_munge_functions.plfh", MockPLFH)

def test_is_date_valid():
    assert is_date_valid("2023-09-21") is True
    assert is_date_valid("1970-01-01") is True
    assert is_date_valid("1969-12-31") is False  # Out of the valid date range
    assert is_date_valid("2171-01-01") is False  # Out of the valid date range
    assert is_date_valid("not_a_date") is False

def test_extract_dates():
    # Test with a string containing multiple date formats
    test_string = "The date is 2023-09-21, and also 09-21-2023 or 20230921"
    result = extract_dates(test_string)
    expected = ["2023-09-21"]
    assert result == expected

    # Test with an invalid date string
    test_string = "No dates here!"
    result = extract_dates(test_string)
    assert result == []

    # Test with malformed but valid dates
    test_string = "The valid dates are 4212024 and 21-Apr-2023"
    result = extract_dates(test_string)
    expected = ["2023-04-21", "2024-04-21"]
    assert result == expected

def test_extract_date_from_filename():
    # Test with a filename that contains multiple date formats
    filename = "report_2023-09-21_final_09212023.txt"
    result = extract_date_from_filename(filename)
    expected = ["2023-09-21"]
    assert result == expected

    # Test with no valid date in the filename
    filename = "report_no_date.txt"
    result = extract_date_from_filename(filename)
    assert result == []

def test_archive_original_file(tmp_path):
    # Set up test paths using pytest's tmp_path fixture
    input_file = tmp_path / "test_input.txt"
    output_file = tmp_path / "archive" / "test_input.txt"

    # Create a dummy input file
    input_file.write_text("Test content")

    # Test archiving the file
    archive_original_file(input_file, output_file)

    # Verify that the file was moved
    assert not input_file.exists()
    assert output_file.exists()

def test_print_pdf_using_os_subprocess(monkeypatch):
    # Mock subprocess.run
    def mock_run(args, **kwargs):
        assert args == [
            "C:\\Users\\Conrad\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe",
            "-print-to", "Test_Printer", "test.pdf"
        ]

    monkeypatch.setattr("subprocess.run", mock_run)

    # Call the function
    print_pdf_using_os_subprocess("test.pdf", "Test_Printer")

if __name__ == "__main__":
    pytest.main()
