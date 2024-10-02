from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates
from generic_pdf_functions import print_pdf, load_pdf_to_dataframe
from generic_dataframe_functions import print_dataframe_to_named_printer
from generic_munge_functions import archive_original_file

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_SUFFIX = ".pdf"
OUTPUT_FILE_SUFFIX = ".pdf"  # if this handler will output a different file type

FILENAME_STRINGS_TO_MATCH = [
    "ttinvoicestouchtunescom",  # This should catch any invoices sent from TouchTunes
    "_e_sum_bill",  # This is the monthly revenue report from jukebox plays
]

ARCHIVE_DIRECTORY_NAME = (
    "pdf_activity_history"
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
    logger.debug(f"Found Date: {filedates_list}")

    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_SUFFIX}")
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        logger.debug(f'Starting data aquisition.')
        raw_dataframe = aquire_data(file_path, filedates_list)
        print_dataframe_to_named_printer(raw_dataframe, SYSTEM_PRINTER_NAME)
        print_pdf(file_path, SYSTEM_PRINTER_NAME, page_range='1')
    except Exception as e:
        logger.error(f"Failure processing PDF: {e}")
        return False
    if not output_file.exists():
        logger.error(f"No data found to process")
        return False

    # TODO move PDF file to archive directory
    input_file_archive_destination = file_path.parent / ARCHIVE_DIRECTORY_NAME
    try:
        logger.info(f"Archiving original file from:\n {file_path} to \n{input_file_archive_destination}")
        archive_original_file(file_path, input_file_archive_destination)
    except Exception as e:
        logger.error(f"Error archiving file: {file_path}, Error: {e}")
        return False

    logger.info(f"All processing for file: {file_path} completed successfully")

    return True


def aquire_data(file_path, filedates_list): 
    data_frame = load_pdf_to_dataframe(file_path)
    return data_frame


# Example usage
if __name__ == "__main__":
    pdf_file = "example.pdf"  # Replace with your PDF file
    printer = "Your Printer Name"  # Replace with your printer name
    print_pdf(pdf_file, printer)
