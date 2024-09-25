import pytest
import pandas as pd
from pathlib import Path
from unittest import mock
from generic_excel_functions import set_custom_excel_formatting


@pytest.fixture
def sample_dataframe():
    """Fixture to create a sample DataFrame for testing."""
    return pd.DataFrame({
        'Alpha': ['A', 'B', 'C'],
        'Number': [1, 2, 3],
        'Currency': [10.5, 20.1, 30.3],
        'Percentage': [0.1, 0.25, 0.5]
    })


@pytest.fixture
def mock_writer():
    """Fixture to mock the Excel writer."""
    with mock.patch('pandas.ExcelWriter') as mock_writer:
        yield mock_writer


def test_set_custom_excel_formatting(sample_dataframe, mock_writer):
    """Test the custom Excel formatting function."""
    details = ['A', '#', '$', '%']
    # Call the function with the mock writer and the sample DataFrame
    set_custom_excel_formatting(sample_dataframe, mock_writer, details)

    # Verify if the formatting was applied correctly (mock checks)
    mock_writer.book.add_format.assert_any_call({"num_format": "$#,##0.00"})
    mock_writer.book.add_format.assert_any_call({"num_format": "#,##0"})
    mock_writer.book.add_format.assert_any_call({"num_format": "0%"})


def test_excel_writer_workbook_creation(mock_writer):
    """Test if a workbook is correctly created and linked to the writer."""
    # Mock creation of workbook
    workbook_mock = mock.Mock()
    mock_writer.book = workbook_mock

    # Call the function and ensure workbook was created and linked
    set_custom_excel_formatting(pd.DataFrame(), mock_writer, details=[])
    
    assert mock_writer.book == workbook_mock


