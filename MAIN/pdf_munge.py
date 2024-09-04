import subprocess
from pathlib import Path

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
