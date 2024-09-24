import subprocess
from loguru import logger
from pathlib import Path
import pdfplumber
import pandas as pd


@logger.catch()
def convert_html_to_pdf(html_file, output_pdf):
    """
    Converts an HTML file to a PDF using wkhtmltopdf.
    
    :param html_file: Path to the HTML file.
    :param output_pdf: Path where the PDF will be saved.
    """
    wkhtmltopdf_path = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"  # Update this if your wkhtmltopdf is in a different location
    
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
    # -print-to <printer_name> will send the file to the specified printer
    # -print-settings <range> specifies the page range to print
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


@logger.catch()
def load_pdf_to_dataframe(pdf_file):

    # Open the PDF file
    with pdfplumber.open(pdf_file) as pdf:
        # Extract the first page
        first_page = pdf.pages[0]
        
        # Extract tables from the first page
        table = first_page.extract_table()

    # Load the table into a DataFrame
    df = pd.DataFrame(table[1:], columns=table[0])

    return df