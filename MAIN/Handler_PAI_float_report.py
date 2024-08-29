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
from generic_dataframe_functions import extract_date_from_filename
from generic_dataframe_functions import save_results_and_print
from generic_dataframe_functions import data_from_csv
from generic_dataframe_functions import dataframe_contains

# standardized declaration for CFSIV_Data_Munge_Extensible project
FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"
FILENAME_STRINGS_TO_MATCH = [
    "Terminal Status(w_FLOAT)automated",
    "TerminalStatuswFLOATautomated",
    "Terminal_Status_w_FLOAT_automated",
]
ARCHIVE_DIRECTORY_NAME = "FloatReport"


class Declaration:
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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(
            FILE_EXTENSION
        ):
            # match found
            return True
        else:
            # no match
            return False

    def get_filename_strings_to_match(self):
        """Returns the list of filename strings to match"""
        return FILENAME_STRINGS_TO_MATCH


# activate the daclaration
declaration = Declaration()


@logger.catch
def handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template
    if not file_path.exists:
        logger.error(f"File to process does not exist.")
        return False
    else:
        logger.info(f"Looking for date string in: {file_path.stem}")
        filedate = extract_date_from_filename(
            file_path.stem
        )  # filename without extension
        logger.debug(f"Found Date: {filedate}")
        output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
        logger.debug(f"Output filename: {output_file}")
        # launch the processing function
        try:
            result = process_floatReport_csv(file_path, filedate)
            # processing done, send result to printer
        except Exception as e:
            logger.error(f"Failure processing dataframe: {e}")
            return False
        else:
            if len(result) > 0:
                save_results_and_print(output_file, result, file_path)
            else:
                logger.error(f"No data found to process")
                return False
    # all work complete
    return True


@logger.catch
def process_floatReport_csv(in_f, RUNDATE):
    """Scan file and compute sums for 2 columns"""
    empty_df = panda.DataFrame()
    df = data_from_csv(in_f)

    expected_fields_list = [
        "Location",
        "Reject Balance",
        "Balance",
        "Today's Float",
        "Route",
    ]
    actual_columns_found = dataframe_contains(df, expected_fields_list)
    if not (actual_columns_found == expected_fields_list):
        logger.debug(
            f"Data was expected to contain: {expected_fields_list}\n but only these fileds found: {actual_columns_found}"
        )
        return empty_df

    logger.info(f"Data contained all expected fields.")

    # tack on the date of this report extracted from the filename
    df.at[len(df), "Location"] = f"Report ran: {RUNDATE}"

    # Strip out undesirable characters from "Balance" column
    try:
        df["Balance"] = df["Balance"].replace("[\$,)]", "", regex=True)
        df["Balance"] = df["Balance"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in balance column: {e}")
        return empty_df

    # Process "Today's Float" column
    try:
        df.replace({"Today's Float": {"[\$,)]": ""}}, regex=True, inplace=True)
        df["Today's Float"] = panda.to_numeric(df["Today's Float"], errors="coerce")
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
    df.at["Totals", "Location"] = "               Route Totals"

    # work is finished. Drop unneeded columns from output
    df = df.drop(["Route"], axis=1)  # df.columns is zero-based panda.Index

    # sort the data so the totals are listed at the top of the report
    df = df.sort_values("Balance", ascending=False)
    logger.debug(f"Dataframe finished: {df}")
    return df
