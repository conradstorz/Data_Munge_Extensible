"""Handler for PAI report of locations earning a commission for a period.

This code started as the code for 'Process_surcharge'

"""


import pandas as panda
import json
from loguru import logger
from pathlib import Path
from whenever import Instant
from dataframe_functions import save_results_and_print

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

# activate declaration below when script is ready
declaration = Declaration()


@logger.catch
def handler_process(file_path: Path) -> bool:
    # This is the standardized function call for the Data_Handler_Template
    result = empty_df = panda.DataFrame()
    if not file_path.exists:
        logger.error(f'File to process does not exist.')
        return False
    else:
        # process file
        output_file = Path(f'{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}')
        logger.debug(f'Output filename: {output_file}')        
        try:
            Input_df, INPUTDF_TOTAL_ROWS, column_details, terminal_details, LOCATION_TAG = process_monthly_surcharge_report(file_path, Instant.now())
            # processing done, send result to printer
        except Exception as e:
            logger.error(f'Failure processing dataframe: {e}')
            return False
        else:
            # dataframe needs to have additional columns calculated
            new_df = calculate_additional_values(Input_df, terminal_details, column_details)            
            if len(new_df) > 0:
                logger.info(f'Send dataframe to be made into commission report')
                frame = generate_multiple_report_dataframes(column_details, Input_df, INPUTDF_TOTAL_ROWS, LOCATION_TAG)
            else:
                logger.error(f'No data found to process')
                return False
            if len(frame) > 0:
                logger.info(f'Send dataframe to printer')
                for filename, df in frame:
                    save_results_and_print(filename, df, "")  # empty string tells function not to move input file to history
            else:
                logger.error(f'No data frames found to print')
    # all work complete
    return True



# Custom function to serialize the dictionary excluding unserializable objects
def custom_json_serializer(obj):
    # usage example: pretty_dict = json.dumps(dict, default=custom_json_serializer, indent=4)
    if isinstance(obj, (int, float, str, bool, list, tuple, dict, type(None))):
        return obj
    else:
        return str(obj)
    
from customize_dataframe_for_excel import set_custom_excel_formatting

def validate_value(value, min_value=0, max_value=float('inf')):
    """Validate if the value is within the expected range and is not negative.

    Args:
        value (float): The value to validate.
        min_value (float): The minimum acceptable value. Defaults to 0.
        max_value (float): The maximum acceptable value. Defaults to infinity.

    Returns:
        bool: True if value is valid, False otherwise.
    """
    if value < min_value or value > max_value:
        return False
    return True


@logger.catch
def process_monthly_surcharge_report(input_file, RUNDATE):
    """takes a 'csv' file and returns a dataframe
    """
    # pandas tags:
    LOCATION_TAG = "Location"
    DEVICE_NUMBER_TAG = "Device Number"

    DAYS = 30  # most months are 30 days and report covers a month
    # TODO not all reports are 30 days. Some are 90 days. Try to determine actual number of days.
    OPERATING_LABOR = 25  # estimated labor per visit in dollars.
    logger.info("Beginning process of monthly report.")
    logger.info(f"File: {input_file}")

    def moveLast2first(df):
        cols = df.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        return df[cols]

    empty_df = panda.DataFrame() 
    # load the data from filename provided
    try:
        Input_df = panda.read_csv(input_file)
    except Exception as e:
        logger.error(f'Problem using pandas: {e}')
        return (empty_df, 0, "")
    
    INPUTDF_TOTAL_ROWS = len(Input_df)

    logger.info(f"csv file imported into dataframe with {INPUTDF_TOTAL_ROWS} rows.")
    logger.debug(Input_df.columns)

    # TODO combine entries that reference the same terminal in different months.
    #       ...Reports that cover more than 1 month have seperate lines for each monthly period.
    Input_df = Input_df.groupby(
        [Input_df[LOCATION_TAG], Input_df[DEVICE_NUMBER_TAG]], as_index=False
    ).sum(numeric_only=True)

    INPUTDF_TOTAL_ROWS = len(Input_df)

    logger.info(
        f"{INPUTDF_TOTAL_ROWS} rows remain after combining identical locations."
    )

    # slice the terminal numbers and write to temp storage
    try:
        t = Input_df[DEVICE_NUMBER_TAG]
        t.to_json("temp.json", indent=4)
        # TODO use this to determine which new terminals are missing from value lookup
    except KeyError as e:
        logger.error(f"Error {e}")

    with open(VALUE_FILE) as json_data:
        terminal_details = json.load(json_data)
    # this dictionary will contain information about individual terminals
    # Pretty print and log the dictionary item
    pretty_json = json.dumps(terminal_details, default=custom_json_serializer, indent=4)
    logger.debug(f'Printer details report:\n{pretty_json}')

    logger.info(f"Reading formatting file..")
    with open(FORMATTING_FILE) as json_data:
        column_details = json.load(json_data)
    # this dictionary will contain information about formating output values.
    # Pretty print and log the dictionary item
    pretty_json = json.dumps(column_details, default=custom_json_serializer, indent=4)
    logger.debug(f'Printer details report:\n{pretty_json}')

    return (Input_df, INPUTDF_TOTAL_ROWS, column_details, terminal_details, LOCATION_TAG)


""" these are the calculations used for dupont analysis
Commission_due = df['SurWD Trxs'] * terminal_details[VF_KEY_Commissions]
***This is a cheat sheet to values used in a dupont analysis
Annual_Net_Income = (df['Business Total Income'] - Commission_due) * 12       # (annualized)
Annual_WDs = df['SurWD Trxs'] * 12
Annual_Gross_Surcharge = df['Total Surcharge'] * 12
Period_Dispensed_Amount = df['Total Dispensed Amount']
Average_Surcharge = Annual_Net_Income / Annual_WDs
Surcharge_Percentage = Annual_Net_Income / Annual_Gross_Surcharge
Average_Daily_Dispense = Period_Dispensed_Amount / DAYS
Current_Assets = Average_Daily_Dispense * 14 # Float plus Vault
Assets = FIXED_ASSETS + Current_Assets
Asset_Turnover = Annual_Net_Income / Assets
Earnings_BIT = Annual_Net_Income - OPERATING_EXPENSES
Profit_Margin = Earnings_BIT / Annual_Net_Income
R_O_I = Asset_Turnover * Profit_Margin
"""


def calculate_additional_values(df, terminal_details, column_details):
    # Constants
    DAYS = 30
    FIXED_ASSETS = 1000
    OPERATING_EXPENSES = 50
    OPERATING_LABOR = 25 

    VF_KEY_Commission_rate = "Comm Rate paid"

    # These names must match the input dataframe columns
    SURCHXACTS = "Surcharge WDs"
    GROUPDETAILS = "Group"
    LOCATION_TAG = "Location"

    # These names are added to the original input dataframe
    COMMTOBEPAID = "Comm_Due"

    # Helper functions
    def get_commission_due(row):
        device_info = row.get(LOCATION_TAG, 'unknown')
        group = row.get(GROUPDETAILS, 0)
        _, commrate = group.split()
        commrate = float(commrate)
        # commrate = float(device_info.get(VF_KEY_Commission_rate, 0))
        transactions = float(row.get(SURCHXACTS, 0))
        return round(transactions * commrate, 2)

    # Calculations
    df[COMMTOBEPAID] = df.apply(get_commission_due, axis=1)
 
    return df

    # Example usage
    # df = calculate_values(df, terminal_details, column_details)





@logger.catch()
def generate_report_dataframe(column_details, Input_df, INPUTDF_TOTAL_ROWS, LOCATION_TAG):
    """send ATM terminal activity dataframe to file"""

    with open(REPORT_DEFINITIONS_FILE) as json_data:
        report_definitions = json.load(json_data)
    # this dictionary will contain information about individual reports
    # Pretty print and log the dictionary item
    pretty_json = json.dumps(report_definitions, default=custom_json_serializer, indent=4)
    logger.debug(f'Report Definitions File:{pretty_json}')        

    logger.info(f'Generating report:')
    # create a unique filename for each report
    fn = f"_Outputfile{0}.xlsx"
    # Creating an empty Dataframe with column names only

    # fill those columns with data

    logger.info(f'Dataframe with {len(frame[fn])} items created.')
    # insert name of report into dataframe past the last row 
    frame[fn].at[INPUTDF_TOTAL_ROWS + 1, LOCATION_TAG] = report
logger.info(f'Finished creating {len(frame)} reports as dataframes.')
return frame
