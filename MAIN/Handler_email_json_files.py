import re
import requests
import pandas as panda
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates
from generic_munge_functions import archive_original_file
from generic_dataframe_functions import send_dataframe_to_file_as_csv
from generic_dataframe_functions import load_json_to_dataframe

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_SUFFIX = ".json"
OUTPUT_FILE_SUFFIX = ".csv"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "_CFSIV_email_",
    "dummy place holder",
]
ARCHIVE_DIRECTORY_NAME = "eMail_history"
DOWNLOAD_DIRECTORY = Path("D:/Users/Conrad/Downloads/")

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
    logger.info(f'Handler launched on file {file_path}')

    if not file_path.exists:
        logger.error(f"File '{file_path}' to process does not exist.")
        return False

    logger.debug(f"Looking for date string in: {file_path.stem}")
    filedates_list = extract_dates(file_path.stem)  # filename without SUFFIX
    logger.debug(f"Found Date(s): {filedates_list}")

    new_source_data_filename = file_path.parent / ARCHIVE_DIRECTORY_NAME / file_path.name
    logger.debug(f'New path for data archive: {new_source_data_filename}')
    # ensure that the target directory exists
    new_source_data_filename.parent.mkdir(parents=True, exist_ok=True)

    archive_output_file = file_path.parent / ARCHIVE_DIRECTORY_NAME / Path(f"{file_path.stem}{OUTPUT_FILE_SUFFIX}")
    archive_directory_path = file_path.parent / ARCHIVE_DIRECTORY_NAME
    logger.debug(f"Archive for processed file path is: {archive_directory_path}")

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
    send_dataframe_to_file_as_csv(archive_output_file, processed_dataframe)

    logger.debug(f"moving incoming json file to new location.")
    archive_original_file(file_path, archive_directory_path)

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

    logger.debug(f"{output_file} with embeded date string {date_str_list} readyness verified.")

    # *** place custom code here ***

    # There is an email from PayRange that includes a link in the body of the email to the download url for the data that the email references.
    PAYRANGE_EMAIL_BODY_DETAILS_DOWNLOAD_IDENTIFIER = "\r\nDownload\r\n<https://"
    # When this sub-string exists in the body of an email then go ahead and initiate that download.
    if PAYRANGE_EMAIL_BODY_DETAILS_DOWNLOAD_IDENTIFIER in raw_dataframe['body']:
        logger.debug(f'Data download URL found.')
        data_url = extract_download_url(raw_dataframe['body'])
        logger.debug(f'Data URL: {data_url}')
        initiate_download(data_url, download_dir)
        logger.debug('Data download completed.')

    # all work complete
    return raw_dataframe

def extract_download_url(text):
    """
    Extract the URL that directly follows the word 'Download' in the provided text.

    :param text: The text containing the URL.
    :type text: str
    :return: The extracted URL or None if no URL is found.
    :rtype: str or None
    """
    # Regular expression to find a URL directly preceded by 'Download'
    match = re.search(r'Download\s*<\s*(https?://[^\s>]+)\s*>', text, re.IGNORECASE)
    if match:
        return match.group(1)
    else:
        return None    
    


def initiate_download(url, download_dir):
    """
    Download a file from the given URL and save it in the specified directory using pathlib.

    :param url: The URL of the resource to download.
    :type url: str
    :param download_dir: The directory where the downloaded file will be saved.
    :type download_dir: str or Path
    :return: The path to the downloaded file.
    :rtype: Path or None
    """
    # Ensure the download directory exists
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    # Extract the filename from the URL
    filename = url.split('/')[-1]
    
    # Full path to save the file
    file_path = download_dir / filename

    try:
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        
        # Save the file
        with file_path.open('wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"File downloaded successfully: {file_path}")
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the file: {e}")
        return None
