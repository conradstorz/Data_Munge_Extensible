"""Defines common functions used throughout my code
"""

import re
from dateutil.parser import parse, ParserError
import os
import time
from loguru import logger
import pandas as panda
from pathlib import Path
import pathlib_file_methods as plfh

@logger.catch()
def dataframe_contains(df, list):
    """Examine dataframe for existance of columns named in list
    and return list of columns from list that do not exist.
    """
    column_list = df.columns.tolist()
    matched_columns = [col for col in list if col in column_list]
    return matched_columns


@logger.catch()
def data_from_csv(in_f):
    """Import a CSV file into a datframe"""
    empty_df = panda.DataFrame() 
    # load csv file into dataframe
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
def save_results_and_print(outfile: Path, frame, input_filename: Path) -> bool:
    """filename and dataframe are in the output_dict
    """
    try:
        if len(frame) > 0:
            logger.info(f'Sending Float Report to file/print...')
            Send_dataframe_to_file_and_print(outfile, frame)
        else:
            logger.error(f'Dataframe {input_filename} is empty.')
    except Exception as e:
        logger.error(f'Failure processing dataframe: {e}')
    # work finished remove original file from download directory if filename provided.
    if input_filename == "":
        return True
    else:
        # Original path to the file
        old_file_path = input_filename
        # New path where to move the file
        new_file_path = old_file_path.parent / f"{outfile.stem}_history" / old_file_path.name
        # move the file
        plfh.move_file_with_check(old_file_path, new_file_path, exist_ok=True)
        return True


@logger.catch
def extract_date_from_filename(fname):
    """the filename contains the date the report was run
    extract and return the date string
    # TODO find a new way to look for and return anything that looks like a date from a string.
    """
    datestring = "xxxxxxxx"
    logger.info("Processing: " + str(fname))
    parts = str(fname).split('-')
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
def Send_dataframe_to_file_and_print(filename, frame):
    """Takes a dataframe and outputs to excel file then sends to default printer.
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
            # File creation ends here.

        time.sleep(1)  # Allow time for file to save
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
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

