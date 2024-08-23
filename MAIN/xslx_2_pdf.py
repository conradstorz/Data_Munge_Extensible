from pathlib import Path
from loguru import logger
from dataframe_functions import convert_xlsx_2_pdf, print_pdf_using_os_subprocess


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


if __name__ == "__main__":
    main()
