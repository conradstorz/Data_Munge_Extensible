"""Handler for PAI report of locations earning a commission for a period.

data in csv is:
"Location","WD Trxs","Surcharge WDs","Settlement","Group"(2 items; string: group name, float: commission rate)
"""

import pandas as panda
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_date_from_filename
from generic_dataframe_functions import save_dataframe_as_csv_and_print
from generic_dataframe_functions import load_csv_to_dataframe
from generic_dataframe_functions import verify_dataframe_contains

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"
FILENAME_STRINGS_TO_MATCH = ["ATMActivityReportforcommissions", "dummy place holder"]
ARCHIVE_DIRECTORY_NAME = "QuarterlyCommission"
FORMATTING_FILE = Path.cwd() / "MAIN" / "ColumnFormatting.json"
VALUE_FILE = (
    Path.cwd() / "MAIN" / "Terminal_Details.json"
)  # data concerning investment value and commissions due and operational expenses
REPORT_DEFINITIONS_FILE = (
    Path.cwd() / "MAIN" / "SurchargeReportVariations.json"
)  # this dictionary will contain information about individual reports layouts


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


# activate declaration below when script is ready
declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template
    if not file_path.exists:
        logger.error(f"File to process does not exist.")
        return False

    logger.debug(f"Looking for date string in: {file_path.stem}")
    filedate = extract_date_from_filename(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedate}")
    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Output filename: {output_file}")
    # launch the processing function
    try:
        result = process_commission_report(file_path, filedate)
        # processing done, send result to printer
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False
    else:
        if len(result) > 0:
            save_dataframe_as_csv_and_print(output_file, result, file_path)
        else:
            logger.error(f"No data found to process")
            return False
    # all work complete
    return True


@logger.catch
def process_commission_report(input_file, runday):
    """Scan file and compute sums for 2 columns.

    Parameters:
    - input_file: Path to the input CSV file.
    - runday: Date the report was run.

    Returns:
    - A DataFrame with processed commission data or an empty DataFrame if an error occurs.
    """
    # Import data
    try:
        df = panda.read_csv(input_file)
    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
        return panda.DataFrame()  # empty dataframe
    except panda.errors.EmptyDataError:
        logger.error(f"No data found in file: {input_file}")
        return panda.DataFrame()  # empty dataframe

    # Define expected fields
    expected_fields_list = [
        "Location",
        "WD Trxs",
        "Surcharge WDs",
        "Settlement",
        "Group",
    ]

    # Check if expected fields are present
    actual_columns_found = list(df.columns)
    if not all(field in actual_columns_found for field in expected_fields_list):
        logger.debug(
            f"Data was expected to contain: {expected_fields_list}\n"
            f"But only these fields found: {actual_columns_found}"
        )
        return panda.DataFrame()  # empty frame

    logger.debug(f"Data contained all expected fields.")

    # Tack on the date of this report extracted from the filename
    df.at[len(df), "Location"] = f"Report ran: {runday}"

    # Strip out undesirable characters from "Settlement" column and convert to float
    try:
        df["Settlement"] = df["Settlement"].replace("[\$,)]", "", regex=True)
        df["Settlement"] = df["Settlement"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in 'Settlement' column: {e}")
        return panda.DataFrame()  # empty dataframe
    except ValueError as e:
        logger.error(f"ValueError converting 'Settlement' to float: {e}")
        return panda.DataFrame()  # empty dataframe

    # Process "WD Trxs" column
    try:
        df["WD Trxs"] = df["WD Trxs"].replace("[\$,)]", "", regex=True)
        df["WD Trxs"] = panda.to_numeric(df["WD Trxs"], errors="coerce")
    except KeyError as e:
        logger.error(f"KeyError in 'WD Trxs' column: {e}")
        return panda.DataFrame()  # empty dataframe

    # Process "Surcharge WDs" column
    try:
        df["Surcharge WDs"] = panda.to_numeric(
            df["Surcharge WDs"], errors="coerce"
        ).astype("Int64")
    except KeyError as e:
        logger.error(f"KeyError in 'Surcharge WDs' column: {e}")
        return panda.DataFrame()  # empty dataframe

    # Define the regular expression pattern for extracting monetary values
    find_monetary_value = r"^(.*?),?\s*([$]?\d+\.\d+)$"

    # Extract the commission rate from the Group column
    try:
        df[["groupname", "comm_rate"]] = df["Group"].str.extract(find_monetary_value)
    except KeyError as e:
        logger.error(f"KeyError in 'Group' column: {e}")
        return panda.DataFrame()  # empty dataframe

    # Convert commission_rate to float
    try:
        df["comm_rate"] = df["comm_rate"].str.replace("$", "").astype(float)
    except KeyError as e:
        logger.error(f"KeyError in 'comm_rate' column: {e}")
        return panda.DataFrame()  # empty dataframe
    except ValueError as e:
        logger.error(f"ValueError converting string to float: {e}")
        df["comm_rate"] = 0.0

    # Calculate the commission due
    try:
        df["Commission_Due"] = df["comm_rate"] * df["Surcharge WDs"]
    except KeyError as e:
        logger.error(f"KeyError in 'Commission_Due' calculation: {e}")
        return panda.DataFrame()  # empty dataframe

    # Create an entry for the total of all commission_due
    total_commission_due = df["Commission_Due"].sum()
    df.at[len(df), "Commission_Due"] = total_commission_due

    # Sort the data so the totals are listed at the top of the report
    df = df.sort_values("Settlement", ascending=False)

    logger.debug(f"Dataframe finished: {df}")

    # Drop unneeded columns from output
    df = df.drop(["groupname", "Group", "Settlement", "Surcharge WDs"], axis=1)

    return df
