#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Munge spreadsheet data.
Takes and input file Path obj, and output file Path obj,
and a rundate string and then makes calculations and returns an output version
of the spreadsheet in dataframe format.
"""
from pathlib import Path
from whenever import Instant
from dateutil.parser import parse, ParserError
from loguru import logger
import pandas as panda
import numpy as np
import json
# from customize_dataframe_for_excel import set_custom_excel_formatting

FILE_EXTENSION = '.csv'
NAME_UNIQUE = "Terminal Status(w_FLOAT)automated"
NAME_AKA = 'TerminalStatuswFLOATautomated'


@logger.catch
def process(file_path): # This is the standardized functioncall for the Data_Handler_Template
    out_file_path = Path('.')
    output_ext = 'xlsx'
    basename = ''
    # now_date = Instant.now()
    filedate = extract_date(file_path.stem)  # filename without extension
    output_file = determine_output_filename(filedate, basename, output_ext, out_file_path)
    logger.debug(f"Found Date: {filedate}")
    output_dict = process_floatReport_csv(out_file_path, file_path, filedate)
    Send_dataframes_to_file(output_dict, output_file)
    # work finished remove original file from download directory
    # Original path to the file
    old_file_path = file_path
    # New path where to move the file
    new_file_path = old_file_path.parent / "PAI_float_history" / old_file_path.name
    # move the file
    move_file(old_file_path, new_file_path, exist_ok=True)
    # all work complete
    return True


@logger.catch()
def move_file(source_path, destination_path, exist_ok=False):
    """Example usage:
    move_file('old_file.txt', 'new_location/new_file.txt')
    """
    # Ensure that these are Path objects
    source = Path(source_path)
    destination = Path(destination_path)    

    try:
        destination_dir = destination.parent
        # Ensure the destination directory exists
        if exist_ok:
            # create directory if doesn't exist
            destination_dir.mkdir(parents=True, exist_ok=True)
        else:
            # check but do not create
            destination_dir.mkdir(parents=False, exist_ok=False)

        # Ensure the destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Attempt to move the file
        source.rename(destination)
        print(f"Successfully moved {source} to {destination}")

    except FileNotFoundError:
        print(f"Error: The source file {source} does not exist.")
    except PermissionError:
        print(f"Error: Permission denied. Unable to move {source} to {destination}.")
    except IsADirectoryError:
        print(f"Error: {source} is a directory, not a file.")
    except OSError as e:
        print(f"Error: An OS error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@logger.catch
def process_floatReport_csv(out_f, in_f, RUNDATE):
    """Scan file and compute sums for 2 columns"""
    df = panda.read_csv(in_f)
    DF_LAST_ROW = len(df)
    logger.info(f"Excel file imported into dataframe with {DF_LAST_ROW} rows.")
    # Fields: "Location","Reject Balance","Balance","Today's Float","Route"

    # Add some information to dataframe
    # df.at[DF_LAST_ROW, "Reject Balance"] = str(RUNDATE)
    df.at[DF_LAST_ROW, "Location"] = f"Report ran: {RUNDATE}"

    try:
        df["Balance"] = df["Balance"].replace("[\$,)]", "", regex=True)
        df["Balance"] = df["Balance"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in dataframe: {e}")
        return False

    try:
        df.replace({"Today's Float": {"[\$,)]": ""}}, regex=True, inplace=True)
        # (old version) df["Today's Float"].replace("[\$,)]", "", regex=True, inplace=True)
        df["Today's Float"] = panda.to_numeric(df["Today's Float"], errors='coerce')
        # (old version) df["Today's Float"] = df["Today's Float"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in dataframe: {e}")
        return False

    try:
        df["Reject Balance"] = df["Reject Balance"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in dataframe: {e}")
        return False

    # sum the columns
    df.loc["Totals"] = df.select_dtypes(np.number).sum()
    df.at["Totals", "Location"] = "               Route Totals"

    # work is finished. Drop unneeded columns from output
    # TODO expand this to drop all columns except those desired in the report
    df = df.drop(["Route"], axis=1)  # df.columns is zero-based panda.Index

    # sort the data
    df = df.sort_values("Balance", ascending=False)

    indx = 0
    return {f"Outputfile{indx}.xlsx": df}


@logger.catch()
def Send_dataframes_to_file(frames, out_f):
    """Takes a dict of dataframes and outputs them to excel files them sends them to default printer.
    output file path is modified to create a unique filename for each dataframe.
    """
    with open(FORMATTING_FILE) as json_data:
        column_details = json.load(json_data)
    # this dictionary will contain information about individual column data type

    args = sys.argv
    for filename, frame in frames.items():
        # extract column names from dataframe
        columns = frame.columns
        # establish excel output object and define column formats
        writer = panda.ExcelWriter(filename, engine="xlsxwriter")
        frame.to_excel(writer, startrow=1, sheet_name="Sheet1", index=False)
        # set output formatting
        set_custom_excel_formatting(frame, writer, column_details)
        logger.info("All work done. Saving worksheet...")
        writer.save()
        # now we print
        if len(args) > 1 and args[1] == "-np":
            logger.info("bypassing print option due to '-np' option.")
            logger.info("bypassing file removal option due to '-np' option.")
            logger.info("exiting program due to '-np' option.")
        else:
            logger.info("Send processed file to printer...")
            try:
                os.startfile(filename, "print")
            except FileNotFoundError as e:
                logger.error(f"File not found: {e}")



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
    parts = str(fname).split()
    # TODO also need to split on '-'s to catch a different type of embeded datestring.
    logger.debug(f"fname split result: {parts}")
    for part in parts:
        try:
            datestring = parse(part).strftime("%Y%m%d")
        except ParserError as e:
            logger.debug(f"Date not found Error: {e}")
    return datestring