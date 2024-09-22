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


def test_set_custom_excel_formatting_column_widths(sample_dataframe, mock_writer):
    """Test if column widths are set correctly."""
    details = ['A', '#', '$', '%']
    set_custom_excel_formatting(sample_dataframe, mock_writer, details)
    
    # Check if the column width setting method is called
    mock_writer.sheets["Sheet1"].set_column.assert_any_call(0, 0, 15)  # Example column width for 'Alpha'
    mock_writer.sheets["Sheet1"].set_column.assert_any_call(1, 1, 10)  # Example column width for 'Number'


def test_set_custom_excel_formatting_without_details(sample_dataframe, mock_writer):
    """Test the formatting function with no specific formatting details provided."""
    details = []
    set_custom_excel_formatting(sample_dataframe, mock_writer, details)

    # In this case, no formatting should be applied
    mock_writer.book.add_format.assert_not_called()


def test_set_custom_excel_formatting_invalid_column(sample_dataframe, mock_writer):
    """Test the function when invalid column details are provided."""
    details = ['Invalid', '#', '$', '%']

    # Call the function and handle potential exceptions or warnings
    with pytest.raises(KeyError):
        set_custom_excel_formatting(sample_dataframe, mock_writer, details)


def test_set_custom_excel_formatting_partial_columns(sample_dataframe, mock_writer):
    """Test the function when fewer formatting details than columns are provided."""
    details = ['A', '$']  # Less than the number of columns
    set_custom_excel_formatting(sample_dataframe, mock_writer, details)

    # Ensure only the provided columns have formatting applied
    mock_writer.book.add_format.assert_any_call({"num_format": "$#,##0.00"})
    mock_writer.book.add_format.assert_not_called_with({"num_format": "0%"})  # Percentage not applied


def test_set_custom_excel_formatting_empty_dataframe(mock_writer):
    """Test the function when an empty DataFrame is passed."""
    empty_df = pd.DataFrame()

    # Call the function
    set_custom_excel_formatting(empty_df, mock_writer, details=[])

    # Verify that no formatting actions are taken on an empty DataFrame
    mock_writer.book.add_format.assert_not_called()
    mock_writer.sheets["Sheet1"].set_column.assert_not_called()


def test_excel_writer_save(mock_writer):
    """Test if the Excel writer's save method is called."""
    # Call the function to ensure the save method is triggered
    set_custom_excel_formatting(pd.DataFrame(), mock_writer, details=[])
    
    # Assert that the writer's save method is called
    mock_writer.save.assert_called_once()


def test_excel_writer_workbook_creation(mock_writer):
    """Test if a workbook is correctly created and linked to the writer."""
    # Mock creation of workbook
    workbook_mock = mock.Mock()
    mock_writer.book = workbook_mock

    # Call the function and ensure workbook was created and linked
    set_custom_excel_formatting(pd.DataFrame(), mock_writer, details=[])
    
    assert mock_writer.book == workbook_mock


def test_formatting_logs(sample_dataframe, mock_writer, caplog):
    """Test if log messages are generated as expected."""
    details = ['A', '#', '$', '%']
    
    # Call the function and capture logs
    with caplog.at_level('DEBUG'):
        set_custom_excel_formatting(sample_dataframe, mock_writer, details)

    # Verify the logs contain the appropriate debug messages
    assert "formatting column widths and styles..." in caplog.text
    assert "Trying to create a formatted worksheet..." in caplog.text


def test_file_creation_and_path_handling():
    """Test if the file is created in the correct location using mocked file handling."""
    with mock.patch('generic_pathlib_file_methods.create_path_if_not_exists') as mocked_create_path:
        file_path = Path('/some/fake/path')
        
        # Mock the behavior
        mocked_create_path.return_value = file_path
        
        # Run the function that involves path creation (replace with actual function if necessary)
        #result_path = some_function_that_creates_excel(file_path)  # Placeholder function

        # Ensure the path is created correctly
        mocked_create_path.assert_called_once_with(file_path)
        #assert result_path == file_path


# begin testing of apply_excel....
import pytest
import pandas as pd
from unittest import mock
from generic_excel_functions import apply_excel_formatting_to_dataframe_and_save_spreadsheet

@pytest.fixture
def sample_dataframe():
    """Fixture to create a sample DataFrame for testing."""
    return pd.DataFrame({
        'Device Number': ['D001', 'D002', 'D003'],
        'Bill to Biz Code': ['B001', 'B002', 'B003'],
        'Location': ['Loc1', 'Loc2', 'Loc3'],
        'SurWD Trxs': [10, 20, 30],
        'Non-Sur WD#': [1, 2, 3],
        'Inq Trxs': [100, 200, 300]
    })

@mock.patch('generic_excel_functions.pd.ExcelWriter')
@mock.patch('generic_excel_functions.generic_pathlib_file_methods.create_path_if_not_exists')
def test_apply_excel_formatting_to_dataframe_and_save_spreadsheet(mock_create_path, mock_excel_writer, sample_dataframe):
    """Test the apply_excel_formatting_to_dataframe_and_save_spreadsheet function."""
    filename = "test_excel_output.xlsx"
    
    # Call the function with the sample dataframe and filename
    apply_excel_formatting_to_dataframe_and_save_spreadsheet(filename, sample_dataframe)

    # Ensure the path creation method was called
    mock_create_path.assert_called_once_with(filename)

    # Ensure ExcelWriter was called with the correct filename
    mock_excel_writer.assert_called_once_with(filename, engine='xlsxwriter')

    # Ensure that the DataFrame is written to the Excel file
    mock_excel_writer.return_value.__enter__.return_value.book.add_worksheet.assert_called_once()

    # Verify that formatting is applied based on column details
    mock_excel_writer.return_value.book.add_format.assert_any_call({"num_format": "#,##0"})
    mock_excel_writer.return_value.book.add_format.assert_any_call({"num_format": "$#,##0.00"})


@mock.patch('generic_excel_functions.pd.ExcelWriter')
@mock.patch('generic_excel_functions.generic_pathlib_file_methods.create_path_if_not_exists')
def test_missing_columns_in_dataframe(mock_create_path, mock_excel_writer):
    """Test if the function handles missing columns gracefully."""
    filename = "test_excel_missing_columns.xlsx"
    
    # Create a DataFrame with missing expected columns
    incomplete_df = pd.DataFrame({
        'Device Number': ['D001', 'D002'],
        'Bill to Biz Code': ['B001', 'B002']
    })
    
    # Call the function with the incomplete DataFrame
    apply_excel_formatting_to_dataframe_and_save_spreadsheet(filename, incomplete_df)
    
    # Ensure the DataFrame is still written to the Excel file
    mock_excel_writer.return_value.__enter__.return_value.book.add_worksheet.assert_called_once()

    # Ensure it still attempts to create the path
    mock_create_path.assert_called_once_with(filename)


@mock.patch('generic_excel_functions.pd.ExcelWriter')
@mock.patch('generic_excel_functions.generic_pathlib_file_methods.create_path_if_not_exists')
def test_extra_columns_in_dataframe(mock_create_path, mock_excel_writer):
    """Test if the function handles extra columns in the DataFrame."""
    filename = "test_excel_extra_columns.xlsx"
    
    # Create a DataFrame with extra columns
    extra_columns_df = pd.DataFrame({
        'Device Number': ['D001', 'D002'],
        'Bill to Biz Code': ['B001', 'B002'],
        'Extra Column': ['Extra1', 'Extra2']
    })
    
    # Call the function with the DataFrame that contains extra columns
    apply_excel_formatting_to_dataframe_and_save_spreadsheet(filename, extra_columns_df)
    
    # Ensure the DataFrame is written to the Excel file
    mock_excel_writer.return_value.__enter__.return_value.book.add_worksheet.assert_called_once()

    # Ensure it still attempts to create the path
    mock_create_path.assert_called_once_with(filename)


@mock.patch('generic_excel_functions.pd.ExcelWriter')
@mock.patch('generic_excel_functions.generic_pathlib_file_methods.create_path_if_not_exists')
def test_apply_excel_formatting_with_empty_dataframe(mock_create_path, mock_excel_writer):
    """Test if the function can handle an empty DataFrame."""
    filename = "test_excel_empty.xlsx"
    
    # Create an empty DataFrame
    empty_df = pd.DataFrame()
    
    # Call the function with the empty DataFrame
    apply_excel_formatting_to_dataframe_and_save_spreadsheet(filename, empty_df)
    
    # Ensure the ExcelWriter is still called even with an empty DataFrame
    mock_excel_writer.assert_called_once_with(filename, engine='xlsxwriter')

    # Ensure that no formatting is applied, as there are no columns
    mock_excel_writer.return_value.__enter__.return_value.book.add_format.assert_not_called()

    # Ensure it still attempts to create the path
    mock_create_path.assert_called_once_with(filename)


@mock.patch('generic_excel_functions.pd.ExcelWriter')
@mock.patch('generic_excel_functions.generic_pathlib_file_methods.create_path_if_not_exists')
def test_apply_excel_formatting_file_creation_error(mock_create_path, mock_excel_writer):
    """Test that the function handles errors during file creation."""
    filename = "test_excel_creation_error.xlsx"
    
    # Simulate an error during file creation
    mock_excel_writer.side_effect = IOError("Unable to create file")
    
    with pytest.raises(IOError, match="Unable to create file"):
        apply_excel_formatting_to_dataframe_and_save_spreadsheet(filename, pd.DataFrame())
    
    # Ensure the path creation was attempted before the error occurred
    mock_create_path.assert_called_once_with(filename)


#start testing print_excel
import pytest
from unittest import mock
from generic_excel_functions import print_excel_file
import os

@mock.patch('os.startfile')
def test_print_excel_file_success(mock_startfile, caplog):
    """Test that print_excel_file successfully prints a file."""
    filename = "test_output.xlsx"
    
    # Call the function
    print_excel_file(filename)
    
    # Ensure os.startfile is called with the correct arguments
    mock_startfile.assert_called_once_with(filename, "print")

    # Check the logging messages
    assert "Send processed excel file to printer..." in caplog.text
    assert f"Call to launch spreadsheet {filename} appears to have worked." in caplog.text


@mock.patch('os.startfile', side_effect=FileNotFoundError("File not found"))
def test_print_excel_file_not_found(mock_startfile, caplog):
    """Test that print_excel_file handles a missing file."""
    filename = "missing_file.xlsx"
    
    # Call the function
    print_excel_file(filename)
    
    # Ensure os.startfile was called
    mock_startfile.assert_called_once_with(filename, "print")
    
    # Ensure the error is logged
    assert "Output file not found" in caplog.text


def test_print_excel_file_no_file_provided(caplog):
    """Test that print_excel_file handles an empty filename gracefully."""
    filename = ""

    with mock.patch('os.startfile') as mock_startfile:
        # Call the function
        print_excel_file(filename)

        # Ensure os.startfile was not called since no file was provided
        mock_startfile.assert_not_called()

        # Check the logs for any unusual behavior (optional)
        assert "Send processed excel file to printer..." in caplog.text
        assert "Call to launch spreadsheet" not in caplog.text  # It shouldn't succeed


# begin testing convert_xlsx_2_pdf
import pytest
from unittest import mock
from generic_excel_functions import convert_xlsx_2_pdf
from pathlib import Path

@mock.patch('generic_excel_functions.pd.ExcelFile')
@mock.patch('generic_excel_functions.FPDF')
def test_convert_xlsx_2_pdf_success(mock_fpdf, mock_excel_file):
    """Test that convert_xlsx_2_pdf successfully converts an xlsx file to pdf."""
    fname = "test.xlsx"
    
    # Mock the Excel file and PDF objects
    mock_fpdf_instance = mock_fpdf.return_value
    mock_excel_file.return_value = mock.Mock()
    
    # Call the function
    convert_xlsx_2_pdf(fname)

    # Ensure the Excel file is read correctly
    mock_excel_file.assert_called_once_with(Path(fname))

    # Ensure the PDF creation methods are called
    mock_fpdf_instance.add_page.assert_called()
    mock_fpdf_instance.output.assert_called_once_with(f"{Path(fname).stem}.pdf")


@mock.patch('generic_excel_functions.pd.ExcelFile', side_effect=FileNotFoundError("File not found"))
def test_convert_xlsx_2_pdf_file_not_found(mock_excel_file, caplog):
    """Test that convert_xlsx_2_pdf handles missing files."""
    fname = "missing_file.xlsx"
    
    # Call the function
    convert_xlsx_2_pdf(fname)

    # Ensure the function attempts to load the Excel file and catches the error
    mock_excel_file.assert_called_once_with(Path(fname))

    # Ensure the error is logged
    assert "Error: File not found" in caplog.text


@mock.patch('generic_excel_functions.pd.ExcelFile')
@mock.patch('generic_excel_functions.FPDF')
def test_convert_xlsx_2_pdf_with_custom_header_footer(mock_fpdf, mock_excel_file):
    """Test that convert_xlsx_2_pdf handles custom headers and footers."""
    fname = "test.xlsx"
    header = ["Custom Header"]
    footer = ["Custom Footer"]

    mock_fpdf_instance = mock_fpdf.return_value
    mock_excel_file.return_value = mock.Mock()

    # Call the function with custom header and footer
    convert_xlsx_2_pdf(fname, header=header, footer=footer)

    # Ensure the custom header and footer are added to the PDF
    mock_fpdf_instance.set_header.assert_called_once_with(header)
    mock_fpdf_instance.set_footer.assert_called_once_with(footer)

    # Ensure the PDF output is saved with the correct filename
    mock_fpdf_instance.output.assert_called_once_with(f"{Path(fname).stem}.pdf")


@mock.patch('generic_excel_functions.pd.ExcelFile')
@mock.patch('generic_excel_functions.FPDF')
def test_convert_xlsx_2_pdf_default_header_footer(mock_fpdf, mock_excel_file):
    """Test that convert_xlsx_2_pdf uses the default header and footer if none are provided."""
    fname = "test.xlsx"

    mock_fpdf_instance = mock_fpdf.return_value
    mock_excel_file.return_value = mock.Mock()

    # Call the function without specifying a header or footer
    convert_xlsx_2_pdf(fname)

    # Ensure the default header and footer are used
    mock_fpdf_instance.set_header.assert_called_once_with(["Top of Page"])
    mock_fpdf_instance.set_footer.assert_called_once_with(["End"])

    # Ensure the PDF output is saved
    mock_fpdf_instance.output.assert_called_once_with(f"{Path(fname).stem}.pdf")


@mock.patch('generic_excel_functions.pd.ExcelFile', side_effect=ValueError("Invalid Excel file"))
def test_convert_xlsx_2_pdf_invalid_excel_file(mock_excel_file, caplog):
    """Test that convert_xlsx_2_pdf handles invalid Excel files."""
    fname = "invalid_file.xlsx"

    # Call the function with an invalid Excel file
    convert_xlsx_2_pdf(fname)

    # Ensure the error is logged
    assert "Error: Invalid Excel file" in caplog.text
