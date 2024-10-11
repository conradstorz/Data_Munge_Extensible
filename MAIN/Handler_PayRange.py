"""PayRange device detail data handler

"""
import pandas as pd
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates
from generic_excel_functions import convert_dataframe_to_excel_with_formatting_and_save
from generic_pathlib_file_methods import move_file_with_check


# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_SUFFIX = ".csv"
OUTPUT_FILE_SUFFIX = ".xlsx"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "-device_detail_(",
    "dummy place holder",
]
ARCHIVE_DIRECTORY_NAME = "PayRange_History"


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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(INPUT_DATA_FILE_SUFFIX):
            return True  # match found
        else:
            return False  # no match

    def get_filename_strings_to_match(self):
        """Returns the list of filename strings to match"""
        return FILENAME_STRINGS_TO_MATCH


# activate declaration below when script is ready
declaration = FileMatcher()


@logger.catch
def data_handler_process(original_file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template
    if not original_file_path.exists:
        logger.error(f"File to process does not appear to exist.")
        return False

    logger.debug(f"Looking for date string(s) in: {original_file_path.stem}")
    filedate_list = extract_dates(original_file_path.stem)  # filename without SUFFIX
    logger.debug(f"Found Date: {filedate_list}")
    archive_input_file_destination = original_file_path.parent / ARCHIVE_DIRECTORY_NAME / Path(f"{original_file_path.name}")
    logger.debug(f"Archive for processed file path is: {archive_input_file_destination}")

    LOCATION_LABEL = 'location'
    columns_to_keep = {  # csv data names and what to change each one to
        'date': "Date",
        LOCATION_LABEL: "Location",
        'machine': "Mach Name",
        'mob_sales': "Mobile$",
        'cash_sales': "Cash$",
        'card_sales': "Credit$",
        # 'tot_sales': "Total$",  The printout is too wide for the printer if all the columns are included
        'net': "Net$",
    }

    # launch the processing function
    df_processed = process_payrange_csv(original_file_path, columns_to_keep, LOCATION_LABEL)
    logger.debug(f'Data processing returned:\n{df_processed=}')

    # Keep only the needed columns
    keep = columns_to_keep.values()  # extract the list of modified names of the columns
    df_processed = df_processed[keep]

    # Add a new row using .loc[] with the same value for all columns
    num_columns = df_processed.shape[1]  # Number of columns in the DataFrame
    df_processed.loc[len(df_processed)] = ['PayRange'] + [''] * (num_columns - 1)    

    # processing done, send result to printer  TODO see if landscape can be specified
    convert_dataframe_to_excel_with_formatting_and_save(Path('temp.xlsx'), df_processed)

    # move file out of downloads
    move_file_with_check(original_file_path, archive_input_file_destination)

    logger.debug(f"\nAll work complete.\n{df_processed}")

    # all work complete
    return True

@logger.catch()
def process_payrange_csv(filename, columns, LOCATION_LABEL):
    """This function written with ChatGPT as a pair programmer.
    """
    # Load the CSV file
    logger.info(f'Loading the CSV file {filename}')
    file_path = Path(filename)
    df = pd.read_csv(file_path)

    # Clean the data by stripping leading/trailing spaces from all columns
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    value = df.iloc[0][LOCATION_LABEL]  # Extract the name of the Business where this data came from

    # Convert the value to a string
    Location_name = str(value)

    logger.debug(f'Data loaded and cleaned for location: {Location_name}.')

    # Drop the last 5 rows of the report. These lines are summary totals of the actual details per machine
    df = df.drop(df.tail(5).index)

    # Rename the columns for clarity 
    for label, new_label in columns.items():
        df.rename(columns={label: new_label}, inplace=True)

    # return the final dataframe
    logger.debug(f'Data processing complete.')
    return df
