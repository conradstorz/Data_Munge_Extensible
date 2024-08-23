import pandas as panda
from fpdf import FPDF
from pathlib import Path
from loguru import logger
import subprocess


@logger.catch()
def load_excel_file(fname):
    try:
        # Load the Excel file
        file_path = Path(fname)
        
        # Ensure the file exists before trying to load it
        if not file_path.exists():
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        
        # Load the Excel file using pandas
        excel_data = panda.ExcelFile(file_path)
        
        # Return the loaded Excel data
        return excel_data
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e} - The file may not be a valid Excel file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@logger.catch()
def convert_xlsx_2_pdf(fname, label=None, footer=None):
    """Converts an xlsx file into a pdf and saves back to same storage as original file.
    header must be a list of strings to be added one per line at the top of the PDF.
    """
    if label == None:
        label = ["Top of Page"]  # Default value

    if footer == None:
        footer = ["End"]  # Default value

    file_path = Path(fname)
    try:
        excel_data = load_excel_file(file_path)
    except Exception as e:
        logger.error(f'Error importing data: {e}')
        return ""
    
    # Read the data from the first sheet
    try:
        data = panda.read_excel(file_path, sheet_name="Sheet1")
    except Exception as e:
        logger.error(f'ERROR reading data: {e}')
        return ""
    
    # Extract the labels and the data
    value_name = data.iloc[0].values
    row_data = data.iloc[1].values

    # Initialize a PDF object
    pdf = FPDF()

    # Add a page to the PDF
    pdf.add_page()

    # Set font for the PDF
    pdf.set_font("Arial", size=12)

    # Add any titles
    for s in label:
        pdf.cell(200, 10, txt=s, ln=True, align="C")

    # Add a line break
    pdf.ln(10)

    # Adding the headers and their corresponding data
    for label, value in zip(value_name, row_data):
        pdf.cell(50, 10, f"{label}: ", border=1)
        pdf.cell(140, 10, f"{value}", border=1, ln=True)

    # Add a line break
    pdf.ln(10)

    # Add any footer
    for s in footer:
        pdf.cell(200, 10, txt=s, ln=True, align="C")

    # Save the PDF to a file
    pdf_output_path = fname.with_suffix(".pdf")
    pdf.output(pdf_output_path)

    print(f"PDF generated successfully at: {pdf_output_path}")
    return pdf_output_path


@logger.catch()
def print_pdf_using_os_subprocess(file_path, printer_name):
    """Print PDF files using the windows program SumatraPDF"""
    subprocess.run(
        [
            "C:\\Users\\Conrad\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe",
            "-print-to",
            printer_name,
            file_path,
        ]
    )


@logger.catch()
def main():
    xslx_path = Path(
        "TouchTunes_Collection_History(0A94D3).xlsx"
    )  # Update this to the correct path if necessary

    pdf_path = convert_xlsx_2_pdf(
        xslx_path,
        label=["TouchTunes Collection History", "Line 2"],
        footer=["bottom", "last line"],
    )

    if pdf_path:
        if pdf_path.exists() == False:
            print(f"PDF file not found")
        else:
            full_path_string = str(pdf_path)
            print_pdf_using_os_subprocess(full_path_string, "Canon TR8500 series")



if __name__ == '__main__':
    main()
