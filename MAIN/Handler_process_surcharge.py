#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Munge spreadsheet data. (process_surcharge)
Takes an input file Path obj, and a rundate string 
and then makes calculations and returns an output version
of the spreadsheet in dataframe format.
"""
"""
# function, download filename, download extension, output extension
BASENAME_BANK_STATEMENT = [process_bank_statement_csv,"BankDepositsStatement", CSV_EXT, CSV_EXT]
EMAIL_BASENAME_FLOATREPORT = [process_floatReport_csv,"Terminal Status(w_FLOAT)automated", CSV_EXT, EXCEL_EXT]
MANUAL_DL_BASENAME_FLOAT_REPORT = [process_floatReport_csv,"TerminalStatuswFLOATautomated3", CSV_EXT, CSV_EXT]
# Report below is called "Simple Summary Report" on PAI website
BASENAME_SIMPLE_SUMMARY = [process_simple_summary_csv,"TerminalTrxData", CSV_EXT, EXCEL_EXT]
# Report below is located in favorite reports and is called "MonthlyRevenueByDevice"
BASENAME_SURCHARGE_MONTHLY_PER_TERMINAL = [process_monthly_surcharge_report_excel,"MonthlyRevenueByDevice",EXCEL_EXT,EXCEL_EXT,]

monthly revenue report headers
"Bill to Business Code","Device Number","Location","SurWD Trxs","Inq Trxs","Denial Trxs","Reversal Trxs","Total Trxs","Total Surcharge","Business Surcharge","Total Interchange","Business Interchange","Business Addl Revenue","Business Credits/Debits","Business Total Income","Non-Sur WD Trxs","Total Dispensed Amount"

"""


import pandas as panda
import json
from loguru import logger
from pathlib import Path
from whenever import Instant
from generic_dataframe_functions import save_results_and_print
from generic_excel_functions import set_custom_excel_formatting, convert_dataframe_to_excel_with_formatting_and_save  # This function is probably in "generic_excel_functions.py" now


# standardized declaration for CFSIV_Data_Munge_Extensible project
FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"
FILENAME_STRINGS_TO_MATCH = [
    "MonthlyRevenueByDevice",
    "ATMActivityReport",
]  # TODO these may need to be different handlers because of different column headings like Terminal Number
ARCHIVE_DIRECTORY_NAME = "MonthlyRevenue"
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


# activate declaration below when script is ready
declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path) -> bool:
    # This is the standardized function call for the Data_Handler_Template
    result = empty_df = panda.DataFrame()
    if not file_path.exists:
        logger.error(f"File to process does not exist.")
        return False
    else:
        # process file
        output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
        logger.debug(f"Output filename: {output_file}")
        try:
            (
                Input_df,
                INPUTDF_TOTAL_ROWS,
                column_details,
                terminal_details,
                LOCATION_TAG,
            ) = process_monthly_surcharge_report(file_path, Instant.now())
            # processing done, send result to printer
        except Exception as e:
            logger.error(f"Failure processing dataframe: {e}")
            return False
        else:
            # dataframe needs to have additional columns calculated
            new_df = calculate_additional_values(
                Input_df, terminal_details, column_details
            )
            if len(new_df) > 0:
                logger.info(f"Send dataframe to be made into various reports")
                frames = generate_multiple_report_dataframes(
                    column_details, new_df, INPUTDF_TOTAL_ROWS, LOCATION_TAG
                )
                logger.debug(f"Frames:\n{frames}")
            else:
                logger.error(f"No data found to process")
                return False
            if len(frames) > 0:
                logger.info(f"Send dataframes to printer")
                for filename, df in frames.items():
                    save_results_and_print(
                        filename, df, ""
                    )  # empty string tells function not to move input file to history
            else:
                logger.error(f"No data frames found to print")
    # all work complete
    return True


# Custom function to serialize the dictionary excluding unserializable objects
def custom_json_serializer(obj):
    # usage example: pretty_dict = json.dumps(dict, default=custom_json_serializer, indent=4)
    if isinstance(obj, (int, float, str, bool, list, tuple, dict, type(None))):
        return obj
    else:
        return str(obj)


def validate_value(value, min_value=0, max_value=float("inf")):
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
    """takes a 'csv' file and returns a dataframe"""
    # pandas tags:
    LOCATION_TAG = "Location"
    DEVICE_NUMBER_TAG = "Terminal"  # changed from 'Device Number' for compatability with "ATM activity report for commissions"

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
        logger.error(f"Problem using pandas: {e}")
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

    # TODO need try/except for missing file detection
    with open(VALUE_FILE) as json_data:
        terminal_details = json.load(json_data)
    # this dictionary will contain information about individual terminals
    # Pretty print and log the dictionary item
    pretty_json = json.dumps(terminal_details, default=custom_json_serializer, indent=4)
    logger.debug(f"Printer details report:\n{pretty_json}")

    logger.info(f"Reading formatting file..")
    # TODO needs try/except for missing file detection
    with open(FORMATTING_FILE) as json_data:
        column_details = json.load(json_data)
    # this dictionary will contain information about formating output values.
    # Pretty print and log the dictionary item
    pretty_json = json.dumps(column_details, default=custom_json_serializer, indent=4)
    logger.debug(f"Printer details report:\n{pretty_json}")

    return (
        Input_df,
        INPUTDF_TOTAL_ROWS,
        column_details,
        terminal_details,
        LOCATION_TAG,
    )


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

    # Column names
    column_names = {
        "BizGrossIncome": "Business Total Income",
        "TOTSUR": "Total Surcharge",
        "TOTDISP": "Total Dispensed Amount",
        "SURCHXACTS": "SurWD Trxs",
        "TOTALXACTS": "Total Trxs",
        "TOTALINTRCHANGE": "Total Interchange",
        "COMM": "Comm_Due",
        "AnnualNetIncome": "Annual_Net_Income",
        "ASURWD": "Annual_SurWDs",
        "SURCH": "_surch",
        "SURCHPER": "_Surch%",
        "DAYDISP": "Daily_Dispense",
        "CURASS": "Current_Assets",
        "ASSETS": "_Assets",
        "ASSETSTO": "A_T_O",
        "ERNBIT": "Earnings_BIT",
        "PRFTMGN": "p_Margin",
        "RTNONINV": "R_O_I",
    }

    LOCATION_TAG = "Location"
    DEVICE_NUMBER_TAG = "Device Number"

    VF_KEY_Owned = "Owned"
    VF_KEY_Value = "Value"
    VF_KEY_VisitDays = "Visit Days"
    VF_KEY_TravelCost = "Travel Cost"
    VF_KEY_SurchargeEarned = "Surcharge Earned"
    VF_KEY_Commission_rate = "Comm Rate paid"

    # These names must match the input dataframe columns
    BizGrossIncome = "Business Total Income"
    TOTSUR = "Total Surcharge"
    TOTDISP = "Total Dispensed Amount"
    SURCHXACTS = "SurWD Trxs"
    TOTALXACTS = "Total Trxs"
    TOTALINTRCHANGE = "Total Interchange"

    # These names are added to the original input dataframe
    COMM = "Comm_Due"
    AnnualNetIncome = "Annual_Net_Income"
    ASURWD = "Annual_SurWDs"
    SURCH = "_surch"
    SURCHPER = "_Surch%"
    DAYDISP = "Daily_Dispense"
    CURASS = "Current_Assets"
    ASSETS = "_Assets"
    ASSETSTO = "A_T_O"
    ERNBIT = "Earnings_BIT"
    PRFTMGN = "p_Margin"
    RTNONINV = "R_O_I"

    # Helper functions
    def get_commission_due(row):
        device_info = terminal_details.get(row.get(DEVICE_NUMBER_TAG, {}), {})
        commrate = float(device_info.get(VF_KEY_Commission_rate, 0))
        transactions = float(row.get(SURCHXACTS, 0))
        return round(transactions * commrate, 2)

    def calculate_annual_net_income(row):
        ta = float(row.get(BizGrossIncome, 0))
        cm = float(row.get(COMM, 0))
        return float((ta - cm) * 12)

    def calculate_annual_surwds(row):
        return int(row.get(SURCHXACTS, 0) * 12)

    def calculate_average_surcharge(row):
        asurwd = float(row.get(ASURWD, 1))
        return round(float(row[AnnualNetIncome]) / asurwd, 2) if asurwd != 0 else 0

    def calculate_surcharge_percentage(row):
        total_surcharge = float(row.get(TOTSUR, 1)) * 12
        return (
            round(float(row[AnnualNetIncome]) / total_surcharge, 2)
            if total_surcharge != 0
            else 0
        )

    def calculate_average_daily_dispense(row):
        return round(float(row.get(TOTDISP, 0)) / DAYS, 2)

    def calculate_current_assets(row):
        device = terminal_details.get(row[DEVICE_NUMBER_TAG], {})
        visits = float(device.get(VF_KEY_VisitDays, 0))
        owned = device.get(VF_KEY_Owned, "Yes")
        if owned == "No":
            return 0
        buffer = 1.5
        return round(float(row[DAYDISP]) * visits * buffer, 2)

    def calculate_assets(row):
        FA = float(
            terminal_details.get(row[DEVICE_NUMBER_TAG], {}).get(VF_KEY_Value, 0)
        )
        return round(FA + float(row[CURASS]), 2)

    def calculate_asset_turnover(row):
        assets = float(row.get(ASSETS, 1))
        return round(float(row[AnnualNetIncome]) / assets, 2) if assets != 0 else 0

    def calculate_earnings_bit(row):
        device = terminal_details.get(row[DEVICE_NUMBER_TAG], {})
        visit = float(device.get(VF_KEY_VisitDays, 1))
        travel_cost = float(device.get(VF_KEY_TravelCost, 0))
        operating_cost = (DAYS / visit) * (travel_cost + OPERATING_LABOR)
        return round(float(row[AnnualNetIncome]) - operating_cost, 2)

    def calculate_profit_margin(row):
        net_income = float(row.get(AnnualNetIncome, 1))
        return round(float(row[ERNBIT]) / net_income, 2) if net_income != 0 else 0

    def calculate_roi(row):
        return round(float(row[ASSETSTO]) * float(row[PRFTMGN]), 2)

    # Calculations
    df[COMM] = df.apply(get_commission_due, axis=1)
    df[AnnualNetIncome] = df.apply(calculate_annual_net_income, axis=1)
    df[ASURWD] = df.apply(calculate_annual_surwds, axis=1)
    df[SURCH] = df.apply(calculate_average_surcharge, axis=1)
    df[SURCHPER] = df.apply(calculate_surcharge_percentage, axis=1)
    df[DAYDISP] = df.apply(calculate_average_daily_dispense, axis=1)
    df[CURASS] = df.apply(calculate_current_assets, axis=1)
    df[ASSETS] = df.apply(calculate_assets, axis=1)
    df[ASSETSTO] = df.apply(calculate_asset_turnover, axis=1)
    df[ERNBIT] = df.apply(calculate_earnings_bit, axis=1)
    df[PRFTMGN] = df.apply(calculate_profit_margin, axis=1)
    df[RTNONINV] = df.apply(calculate_roi, axis=1)

    return df

    # Example usage
    # df = calculate_values(df, terminal_details, column_details)


@logger.catch()
def generate_multiple_report_dataframes(
    column_details, Input_df, INPUTDF_TOTAL_ROWS, LOCATION_TAG
):
    """send ATM terminal activity dataframe to file and printer"""

    with open(REPORT_DEFINITIONS_FILE) as json_data:
        report_definitions = json.load(json_data)
    # this dictionary will contain information about individual reports
    # Pretty print and log the dictionary item
    pretty_json = json.dumps(
        report_definitions, default=custom_json_serializer, indent=4
    )
    logger.debug(f"Report Definitions File:{pretty_json}")

    # create these reports
    DESIRED_REPORTS = ["Commission", "Surcharge", "Dupont"]

    frames = {}
    for indx, report in enumerate(DESIRED_REPORTS):
        logger.info(f"Generating report: {report}")
        # create a unique filename for each report
        fn = f"{report}_Outputfile{indx}.xlsx"
        # Creating an empty Dataframe with column names only
        frames[fn] = panda.DataFrame(columns=report_definitions[report])
        # fill those columns with data
        for column in report_definitions[report]:
            try:
                frames[fn][column] = Input_df[column]
            except KeyError as e:
                logger.error(f"Key Error: {e} column {column} not added")
        logger.info(f"Dataframe with {len(frames[fn])} items created.")
        logger.debug(f"Frame name: {fn}\nFrame data:\n{frames[fn]}")
        # insert name of report into dataframe past the last row
        frames[fn].at[INPUTDF_TOTAL_ROWS + 1, LOCATION_TAG] = report
    logger.info(f"Finished creating {len(frames)} reports as dataframes.")
    return frames
