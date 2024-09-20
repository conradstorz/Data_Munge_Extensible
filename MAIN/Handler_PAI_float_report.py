#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Munge spreadsheet data.
Takes and input file Path obj, and output file Path obj,
and a rundate string and then makes calculations and returns an output version
of the spreadsheet in dataframe format.
"""
from pathlib import Path
from loguru import logger
import pandas as panda
import numpy as np
import time
from generic_excel_functions import apply_excel_formatting_to_dataframe_and_save_spreadsheet
from generic_excel_functions import print_excel_file
from generic_munge_functions import extract_date_from_filename
from generic_dataframe_functions import data_from_csv
from generic_dataframe_functions import dataframe_contains
from generic_munge_functions import archive_original_file


# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"
FILENAME_STRINGS_TO_MATCH = [
    "Terminal Status(w_FLOAT)automated",
    "floatautomated_3_",
    "terminal_statuswfloatautomated",
    ]

ARCHIVE_DIRECTORY_NAME = "FloatReport"


class FileMatcher:
    """
    Declaration for matching files to the script.

    :param filename: Name of the file to match
    :type filename: str
    :return: True if the script matches the file, False otherwise
    :rtype: bool
    """

    @logger.catch()
    def matches(self, filename: Path) -> bool:
        """Define how to match data files"""
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(INPUT_DATA_FILE_EXTENSION):
            return True  # match found
        else:
            return False  # no match

    def get_filename_strings_to_match(self):
        """Returns the list of filename strings to match"""
        return FILENAME_STRINGS_TO_MATCH


# activate the file matcher
declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path):
    # This is the standardized function call for the Data_Handler_Template
    if not file_path.exists():
        logger.error(f"File to process does not exist: {file_path}")
        return False

    file_size = file_path.stat().st_size
    logger.info(f"Starting processing for file: {file_path}, Size: {file_size} bytes")

    logger.debug(f"Looking for date string in: {file_path.stem}")
    try:
        filedate = extract_date_from_filename(file_path.stem)  # filename without extension
        logger.info(f"Extracted Date: {filedate} from filename")
    except Exception as e:
        logger.error(f"Error extracting date from filename: {file_path.stem}, Error: {e}")
        return False

    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Output filename will be: {output_file}")

    archive_input_file = file_path.parent / ARCHIVE_DIRECTORY_NAME / Path(f"{file_path.name}")
    logger.debug(f"Archive for processed file path is: {archive_input_file}")

    # Launch the processing function
    try:
        logger.debug(f"Starting CSV processing for file: {file_path} with date: {filedate}")
        result = process_floatReport_csv(file_path, filedate)
        logger.info(f"CSV processing completed successfully, {len(result)} records found")
    except Exception as e:
        logger.error(f"Failure processing dataframe for file: {file_path}, Error: {e}")
        return False

    if len(result) < 1:
        logger.error(f"No data found to process for file: {file_path}")
        return False

    # Apply formatting rules and save Excel file
    try:
        logger.debug(f"Applying formatting rules to result with {len(result)} records")
        apply_excel_formatting_to_dataframe_and_save_spreadsheet(output_file, result)
        logger.info(f"Successfully saved formatted data to: {output_file}")
    except Exception as e:
        logger.error(f"Error applying formatting or saving the file: {output_file}, Error: {e}")
        return False

    # Introduce a small delay (could be replaced with more reliable checks in the future)
    time.sleep(1)
    
    # Sending file to printer
    try:
        logger.debug(f"Sending Excel file to printer: {output_file}")
        print_excel_file(output_file)
        logger.info(f"Excel file {output_file} sent to printer successfully")
    except Exception as e:
        logger.error(f"Error printing file: {output_file}, Error: {e}")
        return False

    # Archive the original file
    try:
        logger.debug(f"Archiving original file from {file_path} to {archive_input_file}")
        archive_original_file(file_path, archive_input_file)
        logger.info(f"Successfully archived file: {file_path} to {archive_input_file}")
    except Exception as e:
        logger.error(f"Error archiving file: {file_path}, Error: {e}")
        return False

    logger.info(f"All processing for file: {file_path} completed successfully")
    return True



@logger.catch
def process_floatReport_csv(in_f, RUNDATE):
    """Scan file and compute sums for 2 columns"""
    # Declare labels here to eliminate possiblity of typos
    ROUTE_TEXT = "               Route Totals"
    REPORT_DATE = f"Report ran: {RUNDATE}"
    FLOAT_LABEL = "Today's Float"

    empty_df = panda.DataFrame()
    df = data_from_csv(in_f)

    expected_fields_list = [
        "Location",
        "Reject Balance",
        "Balance",
        FLOAT_LABEL,
        "Route",
    ]
    actual_columns_found = dataframe_contains(df, expected_fields_list)
    if not (actual_columns_found == expected_fields_list):
        logger.debug(f"Data was expected to contain: {expected_fields_list}\n but only these fileds found: {actual_columns_found}")
        return empty_df

    logger.debug(f"Data contained all expected fields.")

    # tack on the date of this report extracted from the filename
    df.at[len(df), "Location"] = REPORT_DATE

    # Strip out undesirable characters from "Balance" column
    try:
        df["Balance"] = df["Balance"].replace("[\$,)]", "", regex=True)
        df["Balance"] = df["Balance"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in balance column: {e}")
        return empty_df

    # Process FLOAT_LABEL column
    try:
        df.replace({FLOAT_LABEL: {"[\$,)]": ""}}, regex=True, inplace=True)
        df[FLOAT_LABEL] = panda.to_numeric(df[FLOAT_LABEL], errors="coerce")
    except KeyError as e:
        logger.error(f"KeyError in 'Todays' Float' column: {e}")
        return empty_df

    # Process "Reject Balance" column
    try:
        df["Reject Balance"] = df["Reject Balance"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in 'Reject Balance' column: {e}")
        return empty_df

    # sum the columns
    df.loc["Totals"] = df.select_dtypes(np.number).sum()
    df.at["Totals", "Location"] = ROUTE_TEXT

    # sum the sums
    # Locate the row containing "Route Totals"
    route_totals_row = df[df['Location'].str.contains('Route Totals', na=False)]

    # Sum the relevant values from "Route Totals" row
    sum_value = route_totals_row['Balance'].values[0] + route_totals_row[FLOAT_LABEL].values[0]
    print(f'{sum_value=}')
    # Locate the row containing "Report Ran" and place the sum in the "Balance" column
    df.loc[df['Location'].str.contains('Report ran', na=False), 'Balance'] = sum_value


    # work is finished. Drop unneeded columns from output
    df = df.drop(["Route"], axis=1)  # df.columns is zero-based panda.Index

    # sort the data so the totals are listed at the top of the report
    df = df.sort_values("Balance", ascending=False)
    logger.debug(f"Dataframe finished: {df}")
    return df
