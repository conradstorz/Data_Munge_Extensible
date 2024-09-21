import re
from datetime import datetime
from loguru import logger
import subprocess
from pathlib import Path
import generic_pathlib_file_methods as plfh
from dateutil.parser import parse, ParserError

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

@logger.catch()
def archive_original_file(input_filename: Path, outfile: Path):
    """
    Move the original file to a new location.

    Args:
        input_filename (Path): Original input file name.
        outfile (Path): Path to the output file.
    """
    # move the file
    plfh.move_file_with_check(input_filename, outfile, exist_ok=True)
    logger.debug(f"Moved original file from {input_filename} to {outfile}")

@logger.catch()
def is_date_valid(date_str):
    formats = ["%Y%b%d", "%Y%m%d", "%Y-%m-%d"]
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

@logger.catch()
def extract_dates(string):
    # Define patterns to match different date formats
    patterns = [
        r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})",  # YYYY-MM-DD or YYYY_MM_DD
        r"(\d{1,2})-(\d{1,2})-(\d{4})",  # MM-DD-YYYY
        r"(\d{4})(\d{2})(\d{2})",  # YYYYMMDD
        r"(\d{4})([a-zA-Z]{3})(\d{2})",  # YYYYmonDD
        r"([A-Za-z]+) (\d{1,2}), (\d{4})",  # Month DD, YYYY
        r"\b(\d{1,2})(\d{1,2})(\d{4})\b",  # Handle formats like '4212024'
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
                    month = datetime.strptime(match[1].lower(), "%b").strftime("%m")
                    date_str = f"{match[0]}-{month}-{match[2].zfill(2)}"
                elif pattern == patterns[4]:  # Month DD, YYYY
                    month = datetime.strptime(match[0][:3].lower(), "%b").strftime("%m")
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

@logger.catch()
def extract_date_from_filename(fname):
    """the filename contains the date the report was run.
    extract and return the date string
    # TODO return a list of all dates found in filename
    """
    datestring = "xxxxxxxx"
    logger.debug("Processing: " + str(fname))
    parts = str(fname).replace("_", "-").split("-")
    logger.debug(f"fname split result: {parts}")
    for part in parts:
        try:
            datestring = parse(part).strftime("%Y%m%d")
        except ParserError as e:
            logger.debug(f"Date not found Error: {e}")
    reds = extract_date_from_filename_using_regularExpressions(fname)
    if datestring == "xxxxxxxx":
        if reds == "xxxxxxxx":
            logger.error(f"No datestring found.")
        else:
            return reds
    return datestring

@logger.catch()
def extract_date_from_filename_using_regularExpressions(fname):

    # The filename contains the date the report was run.
    # Extract and return the date string.

    datestring = "xxxxxxxx"
    logger.debug("Processing: " + str(fname))

    # Regular expression patterns for different date formats
    date_patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
        r"\b\d{2}-\d{2}-\d{4}\b",  # DD-MM-YYYY
        r"\b\d{4}_\d{2}_\d{2}\b",  # YYYY_MM_DD
        r"\b\d{2}_\d{2}_\d{4}\b",  # DD_MM_YYYY
        r"\b\d{8}\b",  # YYYYMMDD or DDMMYYYY
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
