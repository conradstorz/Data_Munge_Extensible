#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Munge spreadsheet data.
Takes and input file Path obj, and output file Path obj,
and a rundate string and then makes calculations and returns an output version
of the spreadsheet in dataframe format.
"""
import os
import time
from pathlib import Path
from dateutil.parser import parse, ParserError
from loguru import logger
import pandas as panda
import numpy as np
import CHATGPTMUNGE.pathlib_file_methods as plfh

class Declaration:
    """
    Declaration for matching files to the script.

    :param filename: Name of the file to match
    :type filename: str
    :return: True if the script matches the file, False otherwise
    :rtype: bool
    """
    def matches(self, filename):
        strings_to_match = ["Terminal Status(w_FLOAT)automated", "TerminalStatuswFLOATautomated"]

        if any(s in filename for s in strings_to_match) and filename.endswith('.csv'):
            # match found
            return True
        else:
            # no match
            return False

declaration = Declaration()


@logger.catch
def process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template
    out_file_path = Path(".")
    output_ext = "xlsx"
    basename = ""
    if not file_path.exists:
        logger.error(f'File to process does not exist.')
        return False
    else:
        logger.info(f"Looking for date string in: {file_path.stem}")
        filedate = extract_date(file_path.stem)  # filename without extension
        output_file = determine_output_filename(
            filedate, basename, output_ext, out_file_path
        )
        logger.debug(f"Found Date: {filedate}")
        # launch the processing function
        try:
            output_dict = process_floatReport_csv(out_file_path, file_path, filedate)
            # processing done, send result to printer
            for filename, frame in output_dict.items():
                if len(frame) > 0:
                    logger.info(f'Sending FLoat Report to file/print...')
                    Send_dataframe_to_file(filename, frame)
                else:
                    logger.error(f'Dataframe {filename} is empty.')
        except Exception as e:
            logger.error(f'Failure processing dataframe: {e}')
        # work finished remove original file from download directory
        # Original path to the file
        old_file_path = file_path
        # New path where to move the file
        new_file_path = old_file_path.parent / "PAI_float_history" / old_file_path.name
        # move the file
        plfh.move_file_with_check(old_file_path, new_file_path, exist_ok=True)
    # all work complete
    return True



@logger.catch
def process_floatReport_csv(out_f, in_f, RUNDATE):
    """Scan file and compute sums for 2 columns"""
    # load csv file into dataframe
    try:
        df = panda.read_csv(in_f)
    except Exception as e:
        logger.error(f'Problem using pandas: {e}')
        df = panda.DataFrame()  # empty frame
    else:
        logger.debug(f'imported file processed by pandas okay.')
        DF_LAST_ROW = len(df)
        logger.info(f"file imported into dataframe with {DF_LAST_ROW} rows.")
        # expected Fields: "Location","Reject Balance","Balance","Today's Float","Route"

        # tack on the date of this report extracted from the filename
        df.at[DF_LAST_ROW, "Location"] = f"Report ran: {RUNDATE}"

        # Strip out undesirable characters from "Balance" column
        try:
            df["Balance"] = df["Balance"].replace("[\$,)]", "", regex=True)
            df["Balance"] = df["Balance"].astype(float)
        except KeyError as e:
            logger.error(f"KeyError in balance column: {e}")
            return False

        # Process "Today's Float" column
        try:
            df.replace({"Today's Float": {"[\$,)]": ""}}, regex=True, inplace=True)
            df["Today's Float"] = panda.to_numeric(df["Today's Float"], errors="coerce")
        except KeyError as e:
            logger.error(f"KeyError in 'Todays' Float' column: {e}")
            return False

        # Process "Reject Balance" column
        try:
            df["Reject Balance"] = df["Reject Balance"].astype(float)
        except KeyError as e:
            logger.error(f"KeyError in 'Reject Balance' column: {e}")
            return False

        # sum the columns
        df.loc["Totals"] = df.select_dtypes(np.number).sum()
        df.at["Totals", "Location"] = "               Route Totals"

        # work is finished. Drop unneeded columns from output
        df = df.drop(["Route"], axis=1)  # df.columns is zero-based panda.Index

        # sort the data so the totals are listed at the top of the report
        df = df.sort_values("Balance", ascending=False)
        logger.debug(f'Dataframe finished: {df}')

    return {f"Outputfile0.xlsx": df}


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
def Send_dataframe_to_file(filename, frame):
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
        "Comm_Due": "$",
        "_surch": "$",
        "_Surch%": "%",
        "_Assets": "$",
    }
    # clean up any old output file that exists
    logger.info(f'Clenup any old file left over from previous runs.')
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
        except FileNotFoundError as e:
            logger.error(f"Output file not found: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


# deleting output file before spreadsheet loads and prints will break printing.
"""        # print appears successful, delete output spreadsheet
        if delete_file_if_exists(filename):
            logger.info(f'Output file removed successfully.')
        else:
            logger.info(f'Output file could not be removed.')  """
# current plan is to delete any old file before building new file


@logger.catch
def determine_output_filename(datestr, matchedname, ext, output_folder):
    """Assemble datecode and output folder with original basename into new filename."""
    fn = ""
    # fn = fh.check_and_validate(datestr, output_folder)  # TODO no such function?
    newfilename = Path(f"{fn}_{matchedname}{ext}")
    # TODO check that name does not yet exist, use cfsiv-utils-conradical to avoid filename collisions and auto-renaming.
    return newfilename


@logger.catch
def extract_date(fname):
    """the filename contains the date the report was run
    extract and return the date string
    # TODO use function from cfsiv-utils-conradical to standardize code rather than reinvent it here.
    """
    datestring = "xxxxxxxx"
    logger.info("Processing: " + str(fname))
    parts = str(fname).split('-')
    # TODO also need to split on '-'s to catch a different type of embeded datestring.
    logger.debug(f"fname split result: {parts}")
    for part in parts:
        try:
            datestring = parse(part).strftime("%Y%m%d")
        except ParserError as e:
            logger.debug(f"Date not found Error: {e}")
    return datestring
