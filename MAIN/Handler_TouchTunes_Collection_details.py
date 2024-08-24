import pandas as panda
from loguru import logger
from pathlib import Path

from dataframe_functions import extract_dates
from dataframe_functions import apply_formatting_and_save
from dataframe_functions import convert_xlsx_2_pdf
from dataframe_functions import print_pdf_using_os_subprocess

from TouchTunes_Jukebox_Details import (
    jukebox_data_for_ID,
)  # this is a dictionary constant of IDs and the associated details for all known jukeboxes

SYSTEM_PRINTER_NAME = "Canon TR8500 series"  # SumatrPDF needs the output printer name

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = ".xlsx"  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = [
    "Collection Details (",
    "dummy place holder",
]
ARCHIVE_DIRECTORY_NAME = "TouchTunes_Collection_History"


class Declaration:
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
declaration = Declaration()


@logger.catch
def handler_process(file_path: Path):
    # This is the standardized functioncall for the Data_Handler_Template    
    logger.info(f'Handler launched on file {file_path}')

    if not file_path.exists:
        logger.error(f"File '{file_path}' to process does not exist.")
        return False

    logger.debug(f"Looking for date string in: {file_path.stem}")
    filedates_list = extract_dates(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedates_list}")

    # this data has more needed details in the filename. example:   Collection Details (A79CD) May 17, 2024 (4).csv
    # the jukebox ID is contained inside the first set of parenthesis and needs to be recovered and used to find the location name.
    touchtunes_device = ID_inside_filename(file_path)
    logger.debug(f"Found device ID in filename: Device ID = {touchtunes_device}")

    output_file = Path(
        f"{ARCHIVE_DIRECTORY_NAME}({touchtunes_device}){OUTPUT_FILE_EXTENSION}"
    )
    logger.debug(f"Output filename: {output_file}")

    # launch the processing function
    try:
        logger.debug(f'Starting data aquisition.')
        raw_dataframe = aquire_revenue_data(file_path, filedates_list, touchtunes_device)
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False
    if len(raw_dataframe) < 1:
        logger.error(f"No data found to process")
        return False

    # now generate the output dataframe
    logger.debug(f'Creating custom dataframe for output to printer.')
    df_output = create_output_dataframe_from(raw_dataframe)
    if len(df_output) < 1:
        logger.error(f"No data found to output")
        return False

    # processing done, send result to printer
    headers = [
        "Storz Amusements LLC, Jeffersonville, 812-557-7095",
        "estorz@gmail.com",
        "Jukebox Collection Report",
    ]
    footers = [
        "Thank you for letting me serve you!",
        "Please find Commission check included.",
    ]
    logger.debug(f'Format the data and save to Excel file.')
    outfilename = apply_formatting_and_save(output_file, df_output)

    logger.debug(f'Creating PDF form final output from custom dataframe.')
    outfilename = convert_xlsx_2_pdf(outfilename, header=headers, footer=footers)

    logger.debug(f'Sending PDF to printer using SumatraPDF within Windows.')
    print_pdf_using_os_subprocess(outfilename, SYSTEM_PRINTER_NAME)

    logger.info(f"Output saved as {outfilename}")
    # all jukebox revenue processing work complete
    return True


@logger.catch
def aquire_revenue_data(file_path: Path, dates_list, device_id) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    logger.info(f"Attempting to aquire data for jukebox {device_id}")
    empty_df = panda.DataFrame()

    logger.debug(
        f"{file_path} with embeded date string {dates_list} readyness verified."
    )
    # this csv file is organized with descriptions in column 0 and values in column 1
    """The default download format includes duplicate headers after rotation
        ['1 Credit Jukebox', 'Multi-Credit Jukebox', 'Mobile', 'Karaoke', 'Photobooth', 'Unused credits', 'Cleared credits', 
        'Total Revenue Breakdown', 'Bill', 'Coin', 'Subtotal (Bill + Coin)', 'Linked', 'CC/3rd Party', 'Mobile', 
        'Total Revenue', '1 Credit Jukebox (music)', 'Multi-Credit Jukebox (music)', 'Mobile', 
        'Karaoke service', 'Karaoke BGM', 'Karaoke plays', 'Photobooth print', 'Other fees', 
        'Total Revenues', 'Total fees', 'Total to split', 'Location split', 'Operator split']

        after renaming and adding 2 fields 

        ['1 Credit Jukebox', 'Multi-Credit Jukebox', 'Mobile', 'Karaoke', 'Photobooth', 'Unused credits', 'Cleared credits', 
        'Total Revenue Breakdown', 'Bill', 'Coin', 'Subtotal (Bill + Coin)', 'Linked', 'CC/3rd Party', 'Mobile_1',
        'Total Revenue', '1 Credit Jukebox (music)', 'Multi-Credit Jukebox (music)', 'Mobile_2', 
        'Karaoke service', 'Karaoke BGM', 'Karaoke plays', 'Photobooth print', 'Other fees', 
        'Total Revenues', 'Total fees', 'Total to split', 'Location split', 'Operator split', 'Device_ID', 'Date']
    """
    # Read the CSV file. the structure is   descript,value
    #                                       descript,value
    #                                       ...
    # Read the CSV file with no headers
    try:
        df = panda.read_csv(file_path, header=None)
    except FileNotFoundError as e:
        return empty_df
    logger.debug(f'Dataframe loaded.')

    # Rename the columns for better readability
    df.columns = ["Category", "Value"]
    # Create a dictionary to track the occurrence of each category as we look for duplicate labels
    category_count = {}

    # Function to rename duplicate category labels which we want to avoid
    def rename_duplicate_categories(category):
        if category in category_count:
            category_count[category] += 1
            return f"{category}_{category_count[category]-1}"  # we want zero based labeling
        else:
            category_count[category] = 1
            return category

    # Apply the function to rename categories in the DataFrame
    df["Category"] = df["Category"].apply(rename_duplicate_categories)

    logger.debug(f"Renamed Dataframe:\n{df}")

    # Define the new rows as a list of dictionaries so we can add data to the bottom
    new_rows = [
        {"Category": "Device_ID", "Value": str(device_id)},
        {"Category": "Date",  "Value": dates_list[0]},  # we only want the first date if more than 1 is provided
    ]
    logger.debug(f'{new_rows=}')

    # Create a DataFrame from the new rows
    new_df = panda.DataFrame(new_rows)
    logger.debug(f'{new_df=}')

    # Append the new DataFrame to the original DataFrame
    df_appended = panda.concat([df, new_df], ignore_index=True)
    logger.debug(f"{df_appended=}")

    # Set the first column as the index otherwise we would get the default index numbers as column headers when we rotate
    df = df_appended.set_index(df.columns[0])
    # Rotate the DataFrame 90 degrees to the right
    rotated_df = df.transpose()
    # Reset the index
    rotated_df = rotated_df.reset_index(drop=True)
    logger.debug(f'{rotated_df=}')
    logger.debug(f"{rotated_df.columns.to_list()=}")

    # all dataframe customization complete
    return rotated_df


@logger.catch()
def ID_inside_filename(fn: Path):
    # unique to this data report the ID of the jukebox this data belongs to is only in the download filename
    # get the sub-string inside the parenthesis of the filename which is the jukebox ID
    logger.info(f'Looking for Jukebox ID contained in filename.')
    file_name_string = fn.name
    logger.debug(f"{file_name_string=}")

    parts = file_name_string.split("(")  # Juke ID is prefaced with a parenthesis
    logger.debug(f"{parts=}")
    if len(parts) > 1:
        subparts = parts[1].split(")")
        logger.debug(f"{subparts=}")
        if len(subparts) > 1:
            logger.debug(f"{subparts[0]=}")
            # normalize the ID because the leading zero gets dropped by the in-consistant handling by TouchTunes
            # also found one case where ID did not contain a trailing zero. Handled that edge case manually in the details file.
            if len(subparts[0]) < 6:
                subparts[0] = f"0{subparts[0]}"
            logger.debug(f"{subparts[0]=}")
            return subparts[0]
    return "xxxxxx"  # we failed for some reason


@logger.catch()
def create_output_dataframe_from(df):
    # Remove un-needed columns
    logger.info(f'Building the output dataframe.')

    cols_to_drop = [
        "1 Credit Jukebox",
        "Multi-Credit Jukebox",
        "Karaoke",
        "Photobooth",
        "Unused credits",
        "Cleared credits",
        "Total Revenue Breakdown",
        "Coin",
        "Subtotal (Bill + Coin)",
        "Linked",
        "CC/3rd Party",
        "Mobile_1",
        "Total Revenue",
        "1 Credit Jukebox (music)",
        "Multi-Credit Jukebox (music)",
        "Mobile_2",
        "Karaoke service",
        "Karaoke BGM",
        "Karaoke plays",
        "Photobooth print",
        "Other fees",
    ]
    
    # Check existing columns in the DataFrame
    existing_cols = df.columns.tolist()
    logger.debug(f"{existing_cols=}")

    cols_to_drop_filtered = [col for col in cols_to_drop if col in existing_cols]

    # Drop the filtered columns
    df_dropped = df.drop(columns=cols_to_drop_filtered)
    logger.debug(f"{df_dropped.columns.tolist()=}")
    logger.debug(f"{df_dropped}")
    
    # some of the columns need better names
    df_renamed = df_dropped.rename(columns={
        'Mobile': 'Cellphone Revenue',
        'Bill': 'Cash Money Revenue',
        'Total fees': 'Music License Fees',
        'Location split': 'Your Share',
        'Operator split': 'Storz Share',
    })    
    
    # Add the Location details needed by referencing the Device_ID
    # Device IDs in the dictionary are left padded with 6 zeros
    Dev_ID = df_renamed["Device_ID"].iloc[0]  # Don't understand why this is needed. Extracts the first element
    logger.debug(f"{Dev_ID=}")
    logger.debug(f'"Date" field ={df_renamed["Date"].iloc[0]}')
    # Juke IDs are 12 characters in the database but only 6 in the report
    Juke_ID = f"000000{Dev_ID}"
    logger.debug(f"{Juke_ID=}")
    df_renamed["Location Name"] = jukebox_data_for_ID[Juke_ID]["Location name"]
    # The location name is the only detail available currently from the jukebox details dictionary
    # work complete
    return df_renamed
