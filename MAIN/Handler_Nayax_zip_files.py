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
from generic_munge_functions import archive_original_file
from generic_json_functions import prettify_json

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_SUFFIX = ".zip"
OUTPUT_FILE_SUFFIX = ".json"  # if this handler will output a different file type
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

    logger.debug(f"Looking for date string in: {file_path.stem}")
    filedates_list = extract_dates(file_path.stem)  # filename without SUFFIX or directory tree
    logger.debug(f"Found Date(s): {filedates_list}")

    json_data = get_data_from(file_path)
    logger.debug(f'{json_data=}')
    logger.debug(f'{prettify_json(json_data)}')

    # build output path
    output_filepath = Path(f"{ARCHIVE_DIRECTORY_NAME}\{file_path.stem}{OUTPUT_FILE_SUFFIX}")
    logger.debug(f'{output_filepath=}')

    archive_directory_path = file_path.parent / ARCHIVE_DIRECTORY_NAME
    logger.debug(f"Archive for processed file path is: {archive_directory_path}")    

    processed_json = process_json(json_data, filedates_list, output_filepath)
    logger.debug(f"{prettify_json(processed_json)}")

    # save data

    # print data

    # move data
    logger.debug(f"moving incoming json file to new location.")
    archive_original_file(file_path, archive_directory_path)    

    logger.debug(f"ZIP file processing complete.")
    return True


def process_json(raw_json, filedates_list, output_filepath):
    # return a JSON object ready to use such as print or save.
    logger.debug(f'Begin processing JSON data.')
    if len(raw_json) < 1:
        logger.error(f"No data found to process for output: {output_filepath}")
        return {}
    # add any modification of data desired here such as adding data from filedates_list and output_filepath
    return raw_json


def get_data_from(input_file):
    # read ZIP file content data from file
    logger.debug(f'Attempting to read contents list from ZIP: {input_file}')
    if not input_file.exists:
        logger.error(f"File '{input_file}' to process does not exist.")
        return {}
    # launch the processing function
    logger.debug(f'Starting files list aquisition of: {input_file}')
    try:
        raw_json = sanitize_zip(input_file)
    except FileNotFoundError as e:
        return {}
    logger.debug(f'Zip file contents loaded as a JSON object.')        
    return raw_json


def sanitize_zip(zip_file):
    # Check the contents list of ZIP file in as safe a manner as reasonable
    logger.debug(f'Attempting safe opening of ZIP file: {zip_file}')
    # Define a size limit for files (e.g., 100 MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    # Set the extraction directory
    safe_base_path = Path("/safe/directory/for/extraction")
    file_list = {}
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            for index, info in enumerate(zf.infolist()):
                file_info = {}
                logger.debug(f'{index=},{info=}')
                # Prevent zip bombs by checking uncompressed file size
                if info.file_size > MAX_FILE_SIZE:
                    raise ValueError(f"File {info.filename} exceeds the maximum allowed size.")
                # Avoid directory traversal attacks
                extracted_path = safe_base_path / Path(info.filename)
                if not extracted_path.resolve().is_relative_to(safe_base_path.resolve()):
                    raise ValueError(f"Path traversal detected in file {info.filename}.")
                # Gather file metadata
                file_info["file_name"] = info.filename
                file_info["file_size"] = info.file_size
                file_info["compress_size"] = info.compress_size
                file_info["modified_time"] = datetime(*info.date_time).isoformat()
                file_list[index] = file_info
        # Output JSON data
        json_output = json.dumps(file_list)
    except zipfile.BadZipFile:
        raise ValueError(f"The provided zip file: {zip_file} is malformed or corrupt.")
    return json_output


# Example usage
if __name__ == "__main__":
    zip_file_path = "example.zip"
    json_result = sanitize_zip(zip_file_path)
    print(json_result)
