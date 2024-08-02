"""Handler for PAI report of locations earning a commission for a period.

data in csv is:
"Location","WD Trxs","Surcharge WDs","Settlement","Group"(2 items; string: group name, float: commission rate)
"""


import pandas as panda
from loguru import logger
from pathlib import Path
from dataframe_functions import extract_date_from_filename
from dataframe_functions import save_results_and_print
from dataframe_functions import data_from_csv
from dataframe_functions import dataframe_contains

# standardized declaration for CFSIV_Data_Munge_Extensible project
FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = '.xlsx'
FILENAME_STRINGS_TO_MATCH = ["ATMActivityReportforcommissions", "dummy place holder for more matches in future"]
ARCHIVE_DIRECTORY_NAME = "QuarterlyCommission"
FORMATTING_FILE = Path.cwd() / "MAIN" / "ColumnFormatting.json"
VALUE_FILE = Path.cwd() / "MAIN" / "Terminal_Details.json"  # data concerning investment value and commissions due and operational expenses
REPORT_DEFINITIONS_FILE = Path.cwd() / "MAIN" / "SurchargeReportVariations.json"  # this dictionary will contain information about individual reports layouts

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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(FILE_EXTENSION):
            # match found
            return True
        else:
            # no match
            return False

    def get_filename_strings_to_match(self):
        """Returns the list of filename strings to match"""
        return FILENAME_STRINGS_TO_MATCH


# activate declaration below when script is ready
declaration = Declaration()


@logger.catch
def handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template
    if not file_path.exists:
        logger.error(f'File to process does not exist.')
        return False

    logger.info(f"Looking for date string in: {file_path.stem}")
    filedate = extract_date_from_filename(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedate}")       
    output_file = Path(f'{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}')
    logger.debug(f'Output filename: {output_file}')
    # launch the processing function
    try:
        result = process_commission_report(file_path, filedate)
        # processing done, send result to printer
    except Exception as e:
        logger.error(f'Failure processing dataframe: {e}')
        return False
    else:
        if len(result) > 0:
            save_results_and_print(output_file, result, file_path)
        else:
            logger.error(f'No data found to process')
            return False
    # all work complete
    return True

@logger.catch
def process_commission_report(in_f, RUNDATE):
    """Scan file and compute sums for 2 columns"""
    # import data
    empty_df = panda.DataFrame()
    df = data_from_csv(in_f)
    
    expected_fields_list = ["Location","WD Trxs","Surcharge WDs","Settlement","Group"]

    actual_columns_found = dataframe_contains(df, expected_fields_list)
    
    if not (actual_columns_found == expected_fields_list):
        logger.debug(f'Data was expected to contain: {expected_fields_list}\n but only these fileds found: {actual_columns_found}')
        return empty_df
    
    logger.info(f'Data contained all expected fields.')

    # tack on the date of this report extracted from the filename
    df.at[len(df), "Location"] = f"Report ran: {RUNDATE}"

    # Strip out undesirable characters from "Settlement" column
    try:
        df["Settlement"] = df["Settlement"].replace("[\$,)]", "", regex=True)
        df["Settlement"] = df["Settlement"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in Settlement column: {e}")
        return empty_df

    # Process "WD Trxs" column
    try:
        df.replace({"WD Trxs": {"[\$,)]": ""}}, regex=True, inplace=True)
        df["WD Trxs"] = panda.to_numeric(df["WD Trxs"], errors="coerce")
    except KeyError as e:
        logger.error(f"KeyError in 'WD Trxs' column: {e}")
        return empty_df

    # Process "Surcharge WDs" column
    try:
        # df["Surcharge WDs"] = df["Surcharge WDs"].astype(int)  was throwing exception
        df["Surcharge WDs"] = panda.to_numeric(df["Surcharge WDs"], errors='coerce').astype('Int64')
    except KeyError as e:
        logger.error(f"KeyError in 'Surcharge WDs' column: {e}")
        return empty_df

    # process the "group" column
    # Define the regular expression pattern
    find_monetary_value = r'^(.*?),?\s*([$]?\d+\.\d+)$'

    # Extract the commission_rate from the remainder of the Group column
    try:
        df[['groupname', 'comm_rate']] = df['Group'].str.extract(find_monetary_value)
    except KeyError as e:
        logger.error(f"KeyError in 'Group' column: {e}")
        return empty_df

    # Convert commission_rate to float
    try:
        df['comm_rate'] = df['comm_rate'].str.replace('$', '').astype(float)    
    except KeyError as e:
        logger.error(f"KeyError in 'Surcharge WDs' column: {e}")
        return empty_df
    except ValueError as e:
        logger.error(f'Error converting string to float: {e}')
        df['comm_rate'] = 0.0


    # calculate the commission due
    try:
        df['Commission_Due'] = df['comm_rate'] * df["Surcharge WDs"]    
    except KeyError as e:
        logger.error(f"KeyError in 'Surcharge WDs' column: {e}")
        return empty_df

    # sort the data so the totals are listed at the top of the report
    df = df.sort_values("Settlement", ascending=False)
    logger.debug(f'Dataframe finished: {df}')

    # work is finished. Drop unneeded columns from output
    df = df.drop(["groupname","Group","Settlement", "Surcharge WDs"], axis=1)

    return df
