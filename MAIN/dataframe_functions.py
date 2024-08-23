"""Defines common functions for working with dataframes used throughout my code
"""
from fpdf import FPDF
import subprocess
import re
from datetime import datetime
from dateutil.parser import parse, ParserError
import os
import time
from loguru import logger
import pandas as panda
from pathlib import Path
import pathlib_file_methods as plfh

@logger.catch()
def data_from_csv(in_f):
    """Import a CSV file into a datframe"""
    empty_df = panda.DataFrame() 
    # load csv file into dataframe
    logger.debug(f'Reading CSV data using Pandas on file {in_f}')
    try:
        df = panda.read_csv(in_f)
    except Exception as e:
        logger.error(f'Problem using pandas: {e}')
        return empty_df
    else:
        logger.debug(f'imported file processed by pandas okay.')
        DF_LAST_ROW = len(df)
        logger.info(f"file imported into dataframe with {DF_LAST_ROW} rows.")
        return df


@logger.catch()
def load_csv_with_optional_headers(in_f: str, headers='') -> panda.DataFrame:
    # Set headers to empty list if it's an empty string
    if headers == '':
        headers = []
    else:
        if not isinstance(headers, list):
            logger.error('optional headers field must be a list of strings')
            return panda.DataFrame()  # Return empty DataFrame

    empty_df = panda.DataFrame()  
    # Load CSV file into DataFrame
    try:
        df = panda.read_csv(in_f, header=None if not headers else 0)
    except Exception as e:
        logger.error(f'Problem using pandas: {e}')
        return empty_df
    
    # Handle possible header length mismatch
    if headers:
        num_columns = df.shape[1]
        if len(headers) < num_columns:
            logger.warning(f'Number of headers ({len(headers)}) is less than number of columns ({num_columns}). Numbering missing headers.')
            headers.extend([f'Missing_Header_{i+1}' for i in range(len(headers), num_columns)])  # Number missing headers
        elif len(headers) > num_columns:
            logger.warning(f'Number of headers ({len(headers)}) exceeds number of columns ({num_columns}). Truncating to match.')
            headers = headers[:num_columns]  # Truncate headers to match column count
        df.columns = headers

    return df

@logger.catch()
def dataframe_contains(df, list):
    """Examine dataframe for existance of columns named in list
    and return list of columns from list that do exist.
    """
    column_list = df.columns.tolist()
    matched_columns = [col for col in list if col in column_list]
    return matched_columns


@logger.catch()
def de_duplicate_header_names(df):
    # Rename duplicate columns to ensure uniqueness
    new_columns = []
    column_count = {}
    for col in df.columns:
        if col in column_count:
            column_count[col] += 1
            new_columns.append(f"{col}_{column_count[col]}")
        else:
            column_count[col] = 0
            new_columns.append(col)
    df.columns = new_columns
    logger.debug(f'{new_columns=}')
    return df


@logger.catch()
def save_results_and_print(output_file, result, file_path):
    # This wrapper function is to maintain compatabilitiy with existing code
    save_results(output_file, result, file_path)



@logger.catch()
def save_results(outfile: Path, frame, input_filename: Path) -> bool:
    """
    Save results to a file and manage file movement.
    
    Args:
        outfile (Path): Path to the output file.
        frame (DataFrame): Data to be saved.
        input_filename (Path): Original input file name.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if len(frame) > 0:
            logger.info(f'Sending Float Report to file/print...')
            convert_dataframe_to_excel_with_formatting_and_save(outfile, frame)
        else:
            logger.error(f'Dataframe {input_filename} is empty.')
            return False
    except Exception as e:
        logger.error(f'Failure processing dataframe: {e}')
        return False
    
    if input_filename:
        move_original_file(input_filename, outfile)
    
    return True


def move_original_file(input_filename: Path, outfile: Path):
    """
    Move the original file to a new location.
    
    Args:
        input_filename (Path): Original input file name.
        outfile (Path): Path to the output file.
    """
    # Original path to the file
    old_file_path = input_filename
    # New path where to move the file
    new_file_path = old_file_path.parent / f"{outfile.stem}_history" / old_file_path.name
    
    # move the file
    plfh.move_file_with_check(old_file_path, new_file_path, exist_ok=True)
    logger.info(f'Moved original file from {old_file_path} to {new_file_path}')


def send_dataframe_to_file(outfile: Path, frame):
    # Save the dataframe to a file
    frame.to_csv(outfile, index=False)
    logger.info(f'Dataframe saved to {outfile}')
    

def print_dataframe(frame):
    # Print the dataframe
    logger.info(frame)
    logger.info('Dataframe printed to console')


def Send_dataframe_to_file_and_print(outfile: Path, frame):
    """
    Save the dataframe to a file and print it.
    
    Args:
        outfile (Path): Path to the output file.
        frame (DataFrame): Data to be saved and printed.
    """
    convert_dataframe_to_excel_with_formatting_and_save(outfile, frame)
    send_dataframe_to_file(outfile, frame)
    print_dataframe(frame)


def is_date_valid(date_str):
    formats = ['%Y%b%d', '%Y%m%d', "%Y-%m-%d"]
    min_date = datetime(1970, 1, 1)
    max_date = datetime(2170, 1, 1)    
    for fmt in formats:
        try:
            # Parse the date string
            date_obj = datetime.strptime(date_str, fmt)
            # test the truth of the valid date range
            return min_date <= date_obj <= max_date
        except (TypeError, ValueError) as e:
            continue
    return False


def extract_dates(string):
    # Define patterns to match different date formats
    patterns = [
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # YYYY-MM-DD or YYYY_MM_DD
        r'(\d{1,2})-(\d{1,2})-(\d{4})',      # MM-DD-YYYY
        r'(\d{4})(\d{2})(\d{2})',            # YYYYMMDD
        r'(\d{4})([a-zA-Z]{3})(\d{2})',      # YYYYmonDD
        r'([A-Za-z]+) (\d{1,2}), (\d{4})',   # Month DD, YYYY
        r'\b(\d{1,2})(\d{1,2})(\d{4})\b'     # Handle formats like '4212024'
    ]
    
    found_dates = set()  # Use a set to avoid duplicates
    
    # Try each pattern to find dates
    for pattern in patterns:
        matches = re.findall(pattern, string)
        for match in matches:
            try:
                if pattern == patterns[0]:  # YYYY-MM-DD or YYYY_MM_DD
                    date_str = f"{match[0]}-{match[1].zfill(2)}-{match[2].zfill(2)}"
                elif pattern == patterns[1]:  # MM-DD-YYYY
                    date_str = f"{match[2]}-{match[0].zfill(2)}-{match[1].zfill(2)}"
                elif pattern == patterns[2]:  # YYYYMMDD
                    date_str = f"{match[0]}-{match[1].zfill(2)}-{match[2].zfill(2)}"
                elif pattern == patterns[3]:  # YYYYmonDD
                    month = datetime.strptime(match[1].lower(), '%b').strftime('%m')
                    date_str = f"{match[0]}-{month}-{match[2].zfill(2)}"
                elif pattern == patterns[4]:  # Month DD, YYYY
                    month = datetime.strptime(match[0][:3].lower(), '%b').strftime('%m')
                    date_str = f"{match[2]}-{month}-{match[1].zfill(2)}"
                elif pattern == patterns[5]:  # MMDDYYYY
                    date_str = f"{match[2]}-{match[0].zfill(2)}-{match[1].zfill(2)}"
                
                # Validate and add the date
                if is_date_valid(date_str):
                    found_dates.add(date_str)
            except ValueError:
                continue
    
    # If no valid dates found, return an empty list
    if not found_dates:
        return []

    # Convert the date strings to datetime objects and sort them
    date_objects = [datetime.strptime(date, "%Y-%m-%d") for date in found_dates]
    extracted_dates = sorted(date_objects)

    # Convert the sorted datetime objects back to strings
    sorted_date_strings = [date.strftime("%Y-%m-%d") for date in extracted_dates]

    return sorted_date_strings


@logger.catch
def extract_date_from_filename(fname):
    """the filename contains the date the report was run.
    extract and return the date string
    # TODO return a list of all dates found in filename
    """
    datestring = "xxxxxxxx"
    logger.info("Processing: " + str(fname))
    parts = str(fname).replace("_", "-").split('-')
    logger.debug(f"fname split result: {parts}")
    for part in parts:
        try:
            datestring = parse(part).strftime("%Y%m%d")
        except ParserError as e:
            logger.debug(f"Date not found Error: {e}")
    reds = extract_date_from_filename_using_regularExpressions(fname)
    if datestring == "xxxxxxxx":
        if reds == "xxxxxxxx":
            logger.error(f'No datestring found.')
        else:
            return reds
    return datestring


def extract_date_from_filename_using_regularExpressions(fname):

    # The filename contains the date the report was run.
    # Extract and return the date string.
    
    datestring = "xxxxxxxx"
    logger.info("Processing: " + str(fname))
    
    # Regular expression patterns for different date formats
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{2}-\d{2}-\d{4}\b',  # DD-MM-YYYY
        r'\b\d{4}_\d{2}_\d{2}\b',  # YYYY_MM_DD
        r'\b\d{2}_\d{2}_\d{4}\b',  # DD_MM_YYYY
        r'\b\d{8}\b',              # YYYYMMDD or DDMMYYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, fname)
        if match:
            date_str = match.group()
            logger.debug(f"Found date string: {date_str}")
            try:
                # Attempt to parse the date string
                datestring = parse(date_str).strftime("%Y%m%d")
                break
            except ParserError as e:
                logger.debug(f"Date parsing error: {e}")

    if datestring == "xxxxxxxx":
        logger.debug("No valid date found in filename.")
    
    return datestring


@logger.catch()
def set_custom_excel_formatting(df, writer, details):
    """By default this will expand column widths to display all content.
    Optionally a list of strings defining formats for alpha, numeric, currency or percentage
    may be specified per column. example: ['A','#','$','%'] would set the first 4 columns.
    """
    logger.info("formatting column widths and styles...")

    logger.info("Trying to create a formatted worksheet...")
    # Indicate workbook and worksheet for formatting
    workbook = writer.book
    worksheet = writer.sheets["Sheet1"]

    # Add some cell formats.
    currency_format = workbook.add_format({"num_format": "$#,##0.00"})
    nmbrfrmt = workbook.add_format({"num_format": "#,##0"})
    percntg = workbook.add_format({"num_format": "0%"})

    # Reduce the zoom a little
    worksheet.set_zoom(90)  # does not seem to have any effect

    # Iterate through each column and set the width == the max length in that column. A padding length of 2 is also added.
    for i, col in enumerate(df.columns):
        # find length of column i
        column_width = df[col].astype(str).str.len().max()
        # Setting the length if the column header is larger
        # than the max column value length
        column_width = max(column_width, len(col)) + 2
        if col in details.keys():
            # set the column length and format
            if details[col] == "A":
                worksheet.set_column(i, i, column_width)
            if details[col] == "#":
                worksheet.set_column(i, i, column_width, nmbrfrmt)
            if details[col] == "$":
                worksheet.set_column(i, i, column_width, currency_format)
            if details[col] == "%":
                worksheet.set_column(i, i, column_width, percntg)
        else:  # just set the width of the column
            logger.info(f'No detailed column formating instructions found for: {col}')
            worksheet.set_column(i, i, column_width)
    return True


@logger.catch()
def convert_dataframe_to_excel_with_formatting_and_save(filename, frame):
    """Takes a dataframe and outputs to excel file.
    """
    apply_formatting_and_save(filename, frame)
    time.sleep(1)  # Allow time for file to save
    print_excel_file(filename)


@logger.catch()
def apply_formatting_and_save(filename, frame):
    """Create an excel file on the default storage
    """
    # define the various labels as $ or % or a plain number
    column_details = {
        "Device Number": "A",
        "Bill to Biz Code": "A",
        "Location": "A",
        "SurWD Trxs": "#",
        "Non-Sur WD#": "#",
        "Inq Trxs": "#",
        "Denial Trxs": "#",
        "Reversal Trxs": "#",
        "Total Trxs": "#",
        "Total Surcharge": "$",
        "Total Dispn": "$",
        "Biz Surch": "$",
        "Biz Intchng": "$",
        "Biz Addl Rev": "$",
        "Biz Cred/Debt": "$",
        "Business Total Income": "$",
        "Surch": "$",
        "Avg WD": "$",
        "Surch amt": "$",
        "Settled": "$",
        "DayVaultAVG": "$",
        "Comm Due": "$",
        "An_Net_Incm": "$",
        "An_SurWDs": "#",
        "surch": "$",
        "Surch%": "%",
        "Daily_Disp": "$",
        "Curr_Assets": "$",
        "Assets": "$",
        "A_T_O": "%",
        "Earn_BIT": "$",
        "p_Margin": "%",
        "R_O_I": "%",
        "Annual_Net_Income": "$",
        "Annual_SurWDs": "#",
        "Daily_Dispense": "$",
        "Current_Assets": "$",
        "Earnings_BIT": "$",
        "Commission_Due": "$",
        "_surch": "$",
        "_Surch%": "%",
        "_Assets": "$",
        "Sales($)": "$"
    }
    # clean up any old output file that exists
    logger.info(f'Cleanup any old file left over from previous runs.')
    plfh.delete_file_and_verify(filename)
    try:
        # Create a pandas ExcelWriter object
        logger.debug(f'Creating Excel object {filename} with {len(frame)} lines')
        with panda.ExcelWriter(filename, engine="xlsxwriter") as writer:
            # Write the DataFrame to the Excel file
            logger.debug(f'Writing DataFrame to Excel file')
            frame.to_excel(writer, startrow=1, sheet_name="Sheet1", index=False)
            logger.debug(f'Applying custom column formatting')
            set_custom_excel_formatting(frame, writer, column_details)
            logger.info("All work done. Saving worksheet...")
            # File creation ends here and is saved automatically.

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return filename


def print_excel_file(filename):
    # Now we print
    logger.info("Send processed file to printer...")
    try:
        # this should launch the system spreadsheet program and trigger the print function.
        # A possible failure mode here is that the output goes to the same destination as the last
        # destination used while working with the windows system print dialog which could be the wrong
        # printer or even the print to file option.
        os.startfile(filename, "print")
        logger.debug(f'Call to launch spreadsheet {filename} appears to have worked.')
    except FileNotFoundError as e:
        logger.error(f"Output file not found: {e}")





@logger.catch()
def load_excel_file(fname):
    try:
        # Load the Excel file
        file_path = Path(fname)
        
        # Ensure the file exists before trying to load it
        if not file_path.exists():
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        
        # Load the Excel file using pandas
        excel_data = panda.ExcelFile(file_path)
        
        # Return the loaded Excel data
        return excel_data
    
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
    except ValueError as e:
        logger.error(f"Error: {e} - The file may not be a valid Excel file.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


@logger.catch()
def convert_xlsx_2_pdf(fname, header=None, footer=None):
    """Converts an xlsx file into a pdf and saves back to same storage as original file.
    header must be a list of strings to be added one per line at the top of the PDF.
    """
    if header == None:
        header = ["Top of Page"]  # Default value

    if footer == None:
        footer = ["End"]  # Default value

    file_path = Path(fname)
    try:
        excel_data = load_excel_file(file_path)
    except Exception as e:
        logger.error(f'Error importing data: {e}')
        return ""
    
    # Read the data from the first sheet
    try:
        data = panda.read_excel(file_path, sheet_name="Sheet1")
    except Exception as e:
        logger.error(f'ERROR reading data: {e}')
        return ""
    
    # Extract the labels and the data
    value_name = data.iloc[0].values
    row_data = data.iloc[1].values

    # Initialize a PDF object
    pdf = FPDF()

    # Add a page to the PDF
    pdf.add_page()

    # Set font for the PDF
    pdf.set_font("Arial", size=12)

    # Add any header lines
    for s in header:
        pdf.cell(200, 10, txt=s, ln=True, align="C")

    # Add a line break
    pdf.ln(10)

    # Adding the labels and their corresponding data
    for label, value in zip(value_name, row_data):
        pdf.cell(50, 10, f"{label}: ", border=1)
        pdf.cell(140, 10, f"{value}", border=1, ln=True)

    # Add a line break
    pdf.ln(10)

    # Add any footer
    for s in footer:
        pdf.cell(200, 10, txt=s, ln=True, align="C")

    # Save the PDF to a file
    pdf_output_path = fname.with_suffix(".pdf")
    pdf.output(pdf_output_path)

    logger.info(f"PDF generated successfully at: {pdf_output_path}")
    return pdf_output_path


@logger.catch()
def print_pdf_using_os_subprocess(file_path, printer_name):
    """Print PDF files using the windows program SumatraPDF"""
    subprocess.run(
        [
            "C:\\Users\\Conrad\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe",
            "-print-to",
            printer_name,
            file_path,
        ]
    )
