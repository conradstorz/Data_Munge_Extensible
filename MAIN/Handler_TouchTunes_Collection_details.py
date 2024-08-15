import pandas as pd
from loguru import logger
from pathlib import Path
from dataframe_functions import extract_date_from_filename
from dataframe_functions import save_results_and_print
from dataframe_functions import load_csv_with_optional_headers
from dataframe_functions import extract_dates
from dataframe_functions import de_duplicate_header_names
from TouchTunes_Jukebox_Details import jukebox_data_for_ID  # this is a dictionary constant of IDs and the associated details

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
    if not file_path.exists:
        logger.error(f"File to process does not exist.")
        return False

    logger.info(f"Looking for date string in: {file_path.stem}")
    filedates_list = extract_dates(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedates_list}")

    # this data has more needed details in the filename. example:   Collection Details (A79CD) May 17, 2024 (4).csv
    # the jukebox ID is contained inside the first set of parenthesis and needs to be recovered and used to find the location name.
    touchtunes_device = ID_inside_filename(file_path)
    logger.debug(f'Found device ID in filename: Device ID = {touchtunes_device}')

    output_file = Path(
        f"{ARCHIVE_DIRECTORY_NAME}({touchtunes_device}){OUTPUT_FILE_EXTENSION}"
    )
    logger.debug(f"Output filename: {output_file}")
    
    # launch the processing function
    try:
        result = aquire_this_data(file_path, filedates_list, touchtunes_device)
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False
    if len(result) < 1:
        logger.error(f"No data found to process")
        return False

    # now generate the output dataframe
    df_output = process_df(result)        
    if len(df_output) < 1:
            logger.error(f"No data found to process")
            return False

    # processing done, send result to printer
    # TODO create a nice looking report that can be sent to a customer
    # TODO should probably be a PDF

    save_results_and_print(output_file, df_output, file_path)
    logger.debug(f'\n{df_output}')

    # all work complete
    return True


@logger.catch
def aquire_this_data(file_path: Path, dates_list, device_id) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    logger.debug(f'{device_id=}')
    empty_df = pd.DataFrame()

    logger.info(
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
        df = pd.read_csv(file_path, header=None)
    except FileNotFoundError as e:
        return empty_df

    # Rename the columns for better readability
    df.columns = ['Category', 'Value']

    """ These values are not needed to be converted from strings for my current needs.
    # Convert the 'Value' column from string to float
    df['Value'] = df['Value'].replace('[\$,]', '', regex=True).astype(float)
    """

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
    df['Category'] = df['Category'].apply(rename_duplicate_categories)

    logger.debug(f'{df}')

    # Define the new rows as a list of dictionaries so we can add data to the bottom
    new_rows = [
        {'Category': 'Device_ID', 'Value': str(device_id)},
        {'Category': 'Date', 'Value': dates_list[0]}  # we only want the first date if more than 1 is provided
    ]

    # Create a DataFrame from the new rows
    new_df = pd.DataFrame(new_rows)

    # Append the new DataFrame to the original DataFrame
    df = pd.concat([df, new_df], ignore_index=True)

    logger.debug(f'{df}')

    # Set the first column as the index otherwise we would get the default index numbers as column headers when we rotate
    df = df.set_index(df.columns[0])
    # Rotate the DataFrame 90 degrees to the right
    rotated_df = df.transpose()
    # Reset the index
    rotated_df = rotated_df.reset_index(drop=True)
    logger.debug(f"{rotated_df.columns.to_list()=}")

    # all work complete
    return rotated_df


@logger.catch()
def ID_inside_filename(fn: Path):
    # unique to this data report the ID of the jukebox this data belongs to is only in the download filename
    # get the sub-string inside the parenthesis of the filename which is the jukebox ID
    file_name_string = fn.name
    logger.debug(f'{file_name_string=}')
    parts = file_name_string.split("(")
    logger.debug(f'{parts=}')
    if len(parts) > 1:
        subparts = parts[1].split(")")
        logger.debug(f'{subparts=}')
        if len(subparts) > 1:
            logger.debug(f'{subparts[0]=}')
            # normalize the ID because the leading zero gets dropped by the in-consistant handling by TouchTunes
            if len(subparts[0]) < 6:
                subparts[0] = f"0{subparts[0]}"
            logger.debug(f'{subparts[0]=}')
            return subparts[0]
    return "xxxxxx"  # we failed for some reason


@logger.catch()
def process_df(df):
    # Remove un-needed columns
    cols_to_drop = [
        '1 Credit Jukebox', 
        'Multi-Credit Jukebox', 
        'Karaoke', 
        'Photobooth', 
        'Unused credits', 
        'Cleared credits', 
        'Total Revenue Breakdown', 
        'Coin', 
        'Subtotal (Bill + Coin)', 
        'Linked', 
        'CC/3rd Party', 
        'Mobile_1',
        'Total Revenue', 
        '1 Credit Jukebox (music)', 
        'Multi-Credit Jukebox (music)', 
        'Mobile_2', 
        'Karaoke service', 
        'Karaoke BGM', 
        'Karaoke plays', 
        'Photobooth print', 
        'Other fees', 
    ]
    # Check existing columns in the DataFrame
    existing_cols = df.columns.tolist()
    logger.debug(f"{existing_cols=}")

    cols_to_drop_filtered = [col for col in cols_to_drop if col in existing_cols]

    # Drop the filtered columns
    df_dropped = df.drop(columns=cols_to_drop_filtered)
    logger.debug(f"{df_dropped.columns.tolist()=}")
    logger.debug(f'{df_dropped}')
    # Add the Location details needed by referencing the Device_ID
    # Device IDs in the dictionary are left padded with 6 zeros
    Dev_ID = df_dropped['Device_ID'].iloc[0]  # Extracts the first element
    logger.debug(f'{Dev_ID=}')
    logger.debug(f'"Date" field ={df_dropped["Date"].iloc[0]}')
    Juke_ID = f"000000{Dev_ID}"
    logger.debug(f'{Juke_ID=}')
    df_dropped['Location Name'] = jukebox_data_for_ID[Juke_ID]['Location name']
    # The location name is the only detail available currently from the jukebox details dictionary

    return df_dropped
