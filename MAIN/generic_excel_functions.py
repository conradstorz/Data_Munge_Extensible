import pandas as panda
import os
from pathlib import Path
from loguru import logger
import time
import generic_pathlib_file_methods as plfh
from fpdf import FPDF

@logger.catch()
def set_custom_excel_formatting(df, writer, details):
    """By default this will expand column widths to display all content.
    Optionally a list of strings defining formats for alpha, numeric, currency or percentage
    may be specified per column. example: ['A','#','$','%'] would set the first 4 columns.
    """
    logger.info("formatting column widths and styles...")

    logger.info("Trying to create a formatted worksheet...")
    # Indicate workbook and worksheet for formatting
    workbook = writer.book
    worksheet = writer.sheets["Sheet1"]

    # Add some cell formats.
    currency_format = workbook.add_format({"num_format": "$#,##0.00"})
    nmbrfrmt = workbook.add_format({"num_format": "#,##0"})
    percntg = workbook.add_format({"num_format": "0%"})

    # Reduce the zoom a little
    worksheet.set_zoom(90)  # does not seem to have any effect

    # Iterate through each column and set the width == the max length in that column. A padding length of 2 is also added.
    for i, col in enumerate(df.columns):
        # find length of column i
        column_width = df[col].astype(str).str.len().max()
        # Setting the length if the column header is larger
        # than the max column value length
        column_width = max(column_width, len(col)) + 2
        if col in details.keys():
            # set the column length and format
            if details[col] == "A":
                worksheet.set_column(i, i, column_width)
            if details[col] == "#":
                worksheet.set_column(i, i, column_width, nmbrfrmt)
            if details[col] == "$":
                worksheet.set_column(i, i, column_width, currency_format)
            if details[col] == "%":
                worksheet.set_column(i, i, column_width, percntg)
        else:  # just set the width of the column
            logger.info(f"No detailed column formating instructions found for: {col}")
            worksheet.set_column(i, i, column_width)
    return True


@logger.catch()
def convert_dataframe_to_excel_with_formatting_and_save(filename, frame):
    """Takes a dataframe and outputs to excel file."""
    apply_formatting_and_save(filename, frame)
    time.sleep(1)  # Allow time for file to save
    print_excel_file(filename)


@logger.catch()
def apply_formatting_and_save(filename, frame):
    """Create an excel file on the default storage"""
    # define the various labels as $ or % or a plain number
    column_details = {
        "Device Number": "A",
        "Bill to Biz Code": "A",
        "Location": "A",
        "SurWD Trxs": "#",
        "Non-Sur WD#": "#",
        "Inq Trxs": "#",
        "Denial Trxs": "#",
        "Reversal Trxs": "#",
        "Total Trxs": "#",
        "Total Surcharge": "$",
        "Total Dispn": "$",
        "Biz Surch": "$",
        "Biz Intchng": "$",
        "Biz Addl Rev": "$",
        "Biz Cred/Debt": "$",
        "Business Total Income": "$",
        "Surch": "$",
        "Avg WD": "$",
        "Surch amt": "$",
        "Settled": "$",
        "DayVaultAVG": "$",
        "Comm Due": "$",
        "An_Net_Incm": "$",
        "An_SurWDs": "#",
        "surch": "$",
        "Surch%": "%",
        "Daily_Disp": "$",
        "Curr_Assets": "$",
        "Assets": "$",
        "A_T_O": "%",
        "Earn_BIT": "$",
        "p_Margin": "%",
        "R_O_I": "%",
        "Annual_Net_Income": "$",
        "Annual_SurWDs": "#",
        "Daily_Dispense": "$",
        "Current_Assets": "$",
        "Earnings_BIT": "$",
        "Commission_Due": "$",
        "_surch": "$",
        "_Surch%": "%",
        "_Assets": "$",
        "Sales($)": "$",
    }
    # clean up any old output file that exists
    logger.info(f"Cleanup any old file left over from previous runs.")
    plfh.delete_file_and_verify(filename)
    try:
        # Create a pandas ExcelWriter object
        logger.debug(f"Creating Excel object {filename} with {len(frame)} lines")
        with panda.ExcelWriter(filename, engine="xlsxwriter") as writer:
            # Write the DataFrame to the Excel file
            logger.debug(f"Writing DataFrame to Excel file")
            frame.to_excel(writer, startrow=1, sheet_name="Sheet1", index=False)
            logger.debug(f"Applying custom column formatting")
            set_custom_excel_formatting(frame, writer, column_details)
            logger.info("All work done. Saving worksheet...")
            # File creation ends here and is saved automatically.

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return filename


def print_excel_file(filename):
    # Now we print
    logger.info("Send processed file to printer...")
    try:
        # this should launch the system spreadsheet program and trigger the print function.
        # A possible failure mode here is that the output goes to the same destination as the last
        # destination used while working with the windows system print dialog which could be the wrong
        # printer or even the print to file option.
        os.startfile(filename, "print")
        logger.debug(f"Call to launch spreadsheet {filename} appears to have worked.")
    except FileNotFoundError as e:
        logger.error(f"Output file not found: {e}")


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
        logger.error(f"Error: {e}")
    except ValueError as e:
        logger.error(f"Error: {e} - The file may not be a valid Excel file.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


@logger.catch()
def convert_xlsx_2_pdf(fname, header=None, footer=None):
    """Converts an xlsx file into a pdf and saves back to same storage as original file.
    header must be a list of strings to be added one per line at the top of the PDF.
    """
    if header == None:
        header = ["Top of Page"]  # Default value

    if footer == None:
        footer = ["End"]  # Default value

    file_path = Path(fname)
    try:
        excel_data = load_excel_file(file_path)
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        return ""

    # Read the data from the first sheet
    try:
        data = panda.read_excel(file_path, sheet_name="Sheet1")
    except Exception as e:
        logger.error(f"ERROR reading data: {e}")
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

    # Add any header lines
    for s in header:
        pdf.cell(200, 10, txt=s, ln=True, align="C")

    # Add a line break
    pdf.ln(10)

    # Adding the labels and their corresponding data
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

    logger.info(f"PDF generated successfully at: {pdf_output_path}")
    return pdf_output_path

