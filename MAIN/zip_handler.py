# "notifiernayaxcom_report_"
# ".zip" file

import pandas as panda
from loguru import logger
from pathlib import Path
import zipfile
import json
from pathlib import Path
import os
from datetime import datetime
from generic_munge_functions import extract_dates

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".zip"
OUTPUT_FILE_EXTENSION = ".json"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "notifiernayaxcom_report_",
    "dummy place holder",
]
ARCHIVE_DIRECTORY_NAME = (
    "nayax_sales_history"
)

# This handler processes the zip file provided by nayax credit card processing company

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
# declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template    
    # check filename for datecode
    # gather_data_from_file
    # build_an_output_filepath
    # process_data
    # save_data_if_desired
    # print_data_if_desired
    # move_input_data_file_to_archive

    logger.info(f'ZIP Handler launched on file {file_path}')
    filedates_list = get_dates_from_filename(file_path)
    raw_dataframe = get_data_from(file_path)
    output_filepath = Path(f"{ARCHIVE_DIRECTORY_NAME}\{file_path.stem}{OUTPUT_FILE_EXTENSION}")
    processed_dataframe = process_dataframe(raw_dataframe)
    # save data
    # print data
    # move data
    logger.debug(f"ZIP file processing complete.")
    return True



def process_dataframe(raw_dataframe):
    if len(raw_dataframe) < 1:
        logger.error(f"No data found to process")
        return False

    process_this_data(raw_dataframe, filedates_list, output_file)
    return True




def get_dates_from_filename(input_file):
    logger.debug(f"Looking for date string in: {input_file.stem}")
    filedates_list = extract_dates(input_file.stem)  # filename without extension
    logger.debug(f"Found Date: {filedates_list}")
    return filedates_list



def get_data_from(input_file):
    if not input_file.exists:
        logger.error(f"File '{input_file}' to process does not exist.")
        return False

    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        logger.debug(f'Starting data aquisition.')
        raw_dataframe = aquire_data(input_file, filedates_list)
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False    



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



def sanitize_zip(zip_file):
    # Define a size limit for files (e.g., 100 MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    # Set the extraction directory
    safe_base_path = Path("/safe/directory/for/extraction")

    file_list = []

    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            for info in zf.infolist():
                # Prevent zip bombs by checking uncompressed file size
                if info.file_size > MAX_FILE_SIZE:
                    raise ValueError(f"File {info.filename} exceeds the maximum allowed size.")

                # Avoid directory traversal attacks
                extracted_path = safe_base_path / Path(info.filename)
                if not extracted_path.resolve().is_relative_to(safe_base_path.resolve()):
                    raise ValueError(f"Path traversal detected in file {info.filename}.")

                # Gather file metadata
                file_info = {
                    "file_name": info.filename,
                    "file_size": info.file_size,
                    "compress_size": info.compress_size,
                    "modified_time": datetime(*info.date_time).isoformat(),
                }
                file_list.append(file_info)

        # Output JSON data
        json_output = json.dumps(file_list, indent=4)
        return json_output

    except zipfile.BadZipFile:
        raise ValueError("The provided zip file is malformed or corrupt.")

# Example usage
if __name__ == "__main__":
    zip_file_path = "example.zip"
    json_result = sanitize_zip(zip_file_path)
    print(json_result)
