import pandas as panda
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates
from generic_munge_functions import archive_original_file
from generic_dataframe_functions import send_dataframe_to_file
from generic_dataframe_functions import load_json_to_dataframe

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".json"
OUTPUT_FILE_EXTENSION = ".csv"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "_CFSIV_email_",
    "dummy place holder for more matches in future when there are more than one filename that contains same data",
]
ARCHIVE_DIRECTORY_NAME = "eMail_history"

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
declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template    
    logger.info(f'Handler launched on file {file_path}')

    if not file_path.exists:
        logger.error(f"File '{file_path}' to process does not exist.")
        return False

    logger.debug(f"Looking for date string in: {file_path.stem}")
    filedates_list = extract_dates(file_path.stem)  # filename without extension
    logger.debug(f"Found Date(s): {filedates_list}")

    new_source_data_filename = file_path.parent / ARCHIVE_DIRECTORY_NAME / file_path.name
    logger.debug(f'New path for data archive: {new_source_data_filename}')
    # ensure that the target directory exists
    new_source_data_filename.parent.mkdir(parents=True, exist_ok=True)

    archive_output_file = file_path.parent / ARCHIVE_DIRECTORY_NAME / Path(f"{file_path.stem}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Archive for processed file path is: {archive_output_file}")

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

    logger.debug(f"sending data file to be processed.")
    processed_dataframe = process_this_data(raw_dataframe, filedates_list, file_path)

    logger.debug(f"sending dataframe to storage.")
    send_dataframe_to_file(archive_output_file, processed_dataframe)

    logger.debug(f"moving incoming json file to new location.")
    archive_original_file(file_path, new_source_data_filename)

    return True


@logger.catch
def aquire_data(file_path, filedates_list):
    # load file into dataframe with needed pre-processing
    df = load_json_to_dataframe(file_path)
    logger.debug(f'Dataframe loaded. {df=}')
    # TODO place pre-processing code here
    return df


@logger.catch
def process_this_data(raw_dataframe, date_str_list, output_file) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    empty_df = panda.DataFrame()

    logger.info(f"{output_file} with embeded date string {date_str_list} readyness verified.")
    # *** place custom code here ***

    # all work complete
    return raw_dataframe