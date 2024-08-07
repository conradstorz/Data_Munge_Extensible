import pandas as panda
from loguru import logger
from pathlib import Path
from dataframe_functions import extract_date_from_filename
from dataframe_functions import save_results_and_print
from dataframe_functions import data_from_csv
from dataframe_functions import dataframe_contains

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = '.xlsx'  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = ["dummy_first_filename_string", "dummy place holder for more matches in future when there are more than one filename that contains same data"]
ARCHIVE_DIRECTORY_NAME = "DirectoryNameUsedAsSubDirectoryWhereDataFileIsMovedToAfterProcessing"


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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(INPUT_DATA_FILE_EXTENSION):
            # match found
            return True
        else:
            # no match
            return False

    def get_filename_strings_to_match(self):
        """Returns the list of filename strings to match"""
        return FILENAME_STRINGS_TO_MATCH

# activate declaration below when script is ready
# declaration = Declaration()


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
        result = process_this_data(file_path, filedate)
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
def process_this_data(file_path: Path, date_str) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    empty_df = panda.DataFrame()
    # *** place custom code here ***
    print(f'{file_path} with embeded date string {date_str} readyness verified.')

    # all work complete
    return empty_df
