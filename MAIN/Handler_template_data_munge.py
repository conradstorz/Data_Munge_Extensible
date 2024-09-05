import pandas as panda
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "dummy_first_filename_string",
    "dummy place holder for more matches in future when there are more than one filename that contains same data",
]
ARCHIVE_DIRECTORY_NAME = (
    "DirectoryNameUsedAsSubDirectoryWhereDataFileIsMovedToAfterProcessing"
)


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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(FILE_EXTENSION):
            return True  # match found
        else:
            return False  # no match

    def get_filename_strings_to_match(self):
        """Returns the list of filename strings to match"""
        return FILENAME_STRINGS_TO_MATCH


# activate declaration below when script is ready
# declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template    
    logger.info(f'Handler launched on file {file_path}')

    if not file_path.exists:
        logger.error(f"File '{file_path}' to process does not exist.")
        return False

    logger.debug(f"Looking for date string in: {file_path.stem}")
    filedates_list = extract_dates(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedates_list}")

    

    output_file = Path(
        f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}"
    )
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        logger.debug(f'Starting data aquisition.')
        raw_dataframe = aquire_data(file_path, filedates_list)
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False
    if len(raw_dataframe) < 1:
        logger.error(f"No data found to process")
        return False

    process_this_data(raw_dataframe, filedates_list, output_file)
    return True



@logger.catch
def aquire_data(file_path, filedates_list):
    # load file into dataframe with needed pre-processing
    empty_df = panda.DataFrame()    
    try:
        df = panda.read_csv(file_path, header=None)
    except FileNotFoundError as e:
        return empty_df
    logger.debug(f'Dataframe loaded.')
    return df


@logger.catch
def process_this_data(raw_dataframe, date_str, output_file) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    empty_df = panda.DataFrame()

    # *** place custom code here ***

    logger.debug(f"{output_file} with embeded date string {date_str} readyness verified.")

    # all work complete
    return empty_df
