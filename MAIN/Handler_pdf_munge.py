import subprocess
import pandas as pd
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".pdf"
OUTPUT_FILE_EXTENSION = ".pdf"  # if this handler will output a different file type

FILENAME_STRINGS_TO_MATCH = [
    "STORZCASH_CC_Applied",
    "dummy place holder",
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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(FILE_EXTENSION):
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
    filedates_list = extract_dates(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedates_list}")

    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        logger.debug(f'Starting data aquisition.')
        # raw_dataframe = aquire_data(file_path, filedates_list)
        print_pdf(file_path, SYSTEM_PRINTER_NAME)
    except Exception as e:
        logger.error(f"Failure processing PDF: {e}")
        return False
    if not output_file.exists():
        logger.error(f"No data found to process")
        return False

    return True


def print_pdf(file_path, printer_name, page_range="1-2"):
    """
    Sends a PDF file to the specified printer, printing only the specified page range.
    
    :param file_path: Path to the PDF file.
    :param printer_name: Name of the printer to use.
    :param page_range: Page range to print (default is the first 2 pages: "1-2").
    """
    sumatra_path = r"C:\Program Files\SumatraPDF\SumatraPDF.exe"  # Update this if your SumatraPDF is in a different location
    
    # Verify that the file exists
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    # Construct the command to send to SumatraPDF
    # -print-to <printer_name> will send the file to the specified printer
    # -print-settings <range> specifies the page range to print
    command = [
        sumatra_path,
        '-print-to', printer_name,
        '-print-settings', f'{page_range}',
        str(pdf_path)
    ]
    
    # Execute the command
    try:
        subprocess.run(command, check=True)
        print(f"Sent {page_range} of {file_path} to printer {printer_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to print {file_path}. Error: {e}")



# Example usage
if __name__ == "__main__":
    pdf_file = "example.pdf"  # Replace with your PDF file
    printer = "Your Printer Name"  # Replace with your printer name
    print_pdf(pdf_file, printer)
