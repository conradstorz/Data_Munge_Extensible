# Each handler module should follow a common interface. For example, a handler for PDF files might look like this:
import os
from PyPDF2 import PdfFileReader
import csv
from datetime import datetime

# FILE_EXTENSION will be used by the watcher to find files for this process
FILE_EXTENSION = '.pdf'

# Each data handler will have a function called 'process' that accepts a Path object
def process(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PdfFileReader(file)
            text = ""
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                text += page.extract_text()
        
        data = {"file_name": os.path.basename(file_path), "content": text}
        _save_to_csv(data, file_path)
    except Exception as e:
        print(f"Failed to extract data from {file_path}: {e}")

# functions other than 'process' are for internal use to this script file only.
#       the leading underscore indicates this function is not for use outside of this file.
def _save_to_csv(data, pdf_path):
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{pdf_filename}_{timestamp}.csv"
    csv_file = os.path.join(os.path.expanduser("~/Downloads"), csv_filename)
    
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["file_name", "content"])
        writer.writeheader()
        writer.writerow(data)
    print(f"Data saved to {csv_file}")