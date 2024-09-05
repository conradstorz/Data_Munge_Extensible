
import subprocess
import pandas as pd
from loguru import logger
from pathlib import Path
from generic_munge_functions import extract_dates

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".html"
OUTPUT_FILE_EXTENSION = ".pdf"  # if this handler will output a different file type

FILENAME_STRINGS_TO_MATCH = [
    "sales_activity_by_batch_",
    "dummy place holder",
]

ARCHIVE_DIRECTORY_NAME = (
    "sales_activity_history"
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
    logger.debug(f"Found Date: {filedates_list}")

    

    output_file = Path(f"{ARCHIVE_DIRECTORY_NAME}{OUTPUT_FILE_EXTENSION}")
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        logger.debug(f'Starting data aquisition.')
        # raw_dataframe = aquire_data(file_path, filedates_list)
        convert_html_to_pdf(file_path, output_file)
    except Exception as e:
        logger.error(f"Failure processing HTML: {e}")
        return False
    if not output_file.exists():
        logger.error(f"No data found to process")
        return False

    # process_this_data(raw_dataframe, filedates_list, output_file)
    print_pdf(output_file, SYSTEM_PRINTER_NAME)
    return True


@logger.catch()
def convert_html_to_pdf(html_file, output_pdf):
    """
    Converts an HTML file to a PDF using wkhtmltopdf.
    
    :param html_file: Path to the HTML file.
    :param output_pdf: Path where the PDF will be saved.
    """
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # Update this if your wkhtmltopdf is in a different location
    
    # Verify that the HTML file exists
    html_path = Path(html_file)
    if not html_path.exists():
        raise FileNotFoundError(f"The file {html_file} does not exist.")
    
    # Convert HTML to PDF
    command = [
        wkhtmltopdf_path,
        str(html_path),
        str(output_pdf)
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Successfully converted {html_file} to {output_pdf}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {html_file} to PDF. Error: {e}")


@logger.catch()
def print_pdf(file_path, printer_name, page_range="1-2"):
    """
    Sends a PDF file to the specified printer, printing only the specified page range.
    
    :param file_path: Path to the PDF file.
    :param printer_name: Name of the printer to use.
    :param page_range: Page range to print (default is the first 2 pages: "1-2").
    """
    sumatra_path = r"C:\\Users\\Conrad\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe"  # Update this if your SumatraPDF is in a different location
    
    # Verify that the file exists
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    # Construct the command to send to SumatraPDF
    command = [
        sumatra_path,
        '-print-to', printer_name,
        '-print-settings', f'{page_range}',
        str(pdf_path.resolve())
    ]
    
    # Execute the command
    try:
        subprocess.run(command, check=True)
        print(f"Sent {page_range} of {file_path} to printer {printer_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to print {file_path}. Error: {e}")

"""
@logger.catch
def aquire_data(file_path, filedates_list):
    # load file into dataframe with needed pre-processing
    empty_df = pd.DataFrame()    
    try:
        df = pd.read_csv(file_path, header=None)
    except FileNotFoundError as e:
        return empty_df
    logger.debug(f'Dataframe loaded.')
    return df


@logger.catch
def process_this_data(raw_dataframe, date_str, output_file) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    empty_df = pd.DataFrame()

    # *** place custom code here ***

    logger.debug(f"{output_file} with embeded date string {date_str} readyness verified.")

    # all work complete
    return empty_df
"""

# Example usage

@logger.catch()
def main():
    html_file = "sampl.html"  # Replace with your HTML file
    output_pdf = "output.pdf"  # PDF file after conversion
    printer = "Canon TR8500 series"  # Replace with your printer name
    
    # Convert the HTML to a PDF
    convert_html_to_pdf(html_file, output_pdf)
    
    # Print the first two pages of the generated PDF
    print_pdf(output_pdf, printer)


if __name__ == "__main__":
    main()
