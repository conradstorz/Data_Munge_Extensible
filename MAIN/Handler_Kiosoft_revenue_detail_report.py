import pandas as panda
from loguru import logger
from pathlib import Path
from generic_dataframe_functions import extract_dates
from generic_dataframe_functions import save_results_and_print
from generic_dataframe_functions import data_from_csv
from generic_dataframe_functions import dataframe_contains

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "pay_at_machine_log",
    "dummy place holder",
]
ARCHIVE_DIRECTORY_NAME = "KioSoft_History"


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
            INPUT_DATA_FILE_EXTENSION
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
declaration = Declaration()


@logger.catch
def handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template
    if not file_path.exists:
        logger.error(f"File to process does not exist.")
        return False

    logger.info(f"Looking for date string in: {file_path.stem}")
    filedate_list = extract_dates(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedate_list}")
    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        result = aquire_this_data(file_path, filedate_list)
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False
    if len(result) < 1:
        logger.error(f"No data found to process")
        return False

    # now generate the output dataframe
    df_output = process_df(result)
    if len(df_output) < 1:
        logger.error(f"No data found to process")
        return False

    # processing done, send result to printer
    save_results_and_print(output_file, df_output, file_path)
    logger.debug(f"\n{df_output}")

    # all work complete
    return True


@logger.catch
def aquire_this_data(file_path: Path, filedates: list) -> bool:
    # This is the customized procedures used to process this data
    # data should contain detailed transactions for the period of time described by 'filedates'
    # first date should in the list should be the earlier date and the second date the end date for the reporting period.
    empty_df = panda.DataFrame()  # this is what we reutrn if data connot be imported

    logger.info(f"{file_path} with embeded date string {filedates} readyness verified.")
    # this csv file is organized with descriptions in row 0 and values in row 1-n
    """The default download format:
    ["Date Time","Ultra S/N",Machine,"Machine ID","Location ID","Bank Card Number","Card Type",Location,
    "Transaction Type","Total Amount ($)","Pre-Auth Amount ($)","Set Pre-Auth Amount ($)",Discount,"Special Amt","Response Code"]
    """
    try:
        df = panda.read_csv(file_path)
    except FileNotFoundError as e:
        return empty_df

    logger.debug(f"{df=}")
    # Remove un-needed columns
    cols_to_drop = [
        "Date Time",
        "Ultra S/N",
        "Machine",
        "Location ID",
        "Bank Card Number",
        "Card Type",
        "Transaction Type",
        "Pre-Auth Amount ($)",
        "Set Pre-Auth Amount ($)",
        "Discount",
        "Special Amt",
    ]

    # Check existing columns in the DataFrame
    existing_cols = df.columns.tolist()
    logger.debug(f"{existing_cols=}")
    logger.debug(f"{df.dtypes=}")
    # validate existance of columns before dropping
    cols_to_drop_filtered = [col for col in cols_to_drop if col in existing_cols]
    # Drop the filtered columns
    df_dropped = df.drop(columns=cols_to_drop_filtered)
    # Add the date range field for this report
    if len(filedates) > 1:
        df_dropped["Date Range"] = f"{filedates[0]} / {filedates[1]}"
    else:
        if len(filedates) > 0:
            df_dropped["Date Range"] = f"{filedates[0]}"
    logger.debug(f"{df_dropped.columns.tolist()=}")
    return df_dropped


@logger.catch()
def process_df(df):
    """Now we have a dataframe that contains mulitiple transactions for multiple devices.
    return a dataframe with transactions totaled by device.
    """
    # Filter out rows where 'Response Code' is not 'APPROVAL'
    filtered_df = df[df["Response Code"] == "APPROVAL"]
    logger.debug(
        f"Filtered DataFrame to only include APPROVAL responses. {filtered_df.shape[0]} rows remain."
    )

    # Sort by 'Location', 'Machine ID', and 'Response Code'
    logger.debug(f"{filtered_df.dtypes=}")
    sorted_df = filtered_df.sort_values(by=["Location", "Machine ID", "Response Code"])

    # Calculate the subtotal for each 'Machine ID' for 'Total Amount ($)'
    subtotal_df = (
        sorted_df.groupby("Machine ID").agg({"Total Amount ($)": "sum"}).reset_index()
    )
    subtotal_df = subtotal_df.rename(columns={"Total Amount ($)": "Sales($)"})
    # Merge the subtotal back into the main DataFrame
    merged_df = panda.merge(sorted_df, subtotal_df, on="Machine ID", how="left")

    # Drop duplicates: Keep the first occurrence of each row for a unique set of columns
    unique_columns = ["Location", "Machine ID"]
    deduplicated_df = merged_df.drop_duplicates(subset=unique_columns)

    # Drop the columns no longer needed
    df_dropped = deduplicated_df.drop(columns=["Total Amount ($)", "Response Code"])

    return df_dropped
