import pandas as panda
from loguru import logger
from pathlib import Path
from dataframe_functions import extract_date_from_filename
from dataframe_functions import save_results_and_print
from dataframe_functions import load_csv_with_optional_headers
from dataframe_functions import dataframe_contains

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".csv"
OUTPUT_FILE_EXTENSION = '.xlsx'  # if this handler will output a different file type
FILENAME_STRINGS_TO_MATCH = ["Collection Details (", "dummy place holder for more matches in future when there are more than one filename that contains same data"]
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
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(INPUT_DATA_FILE_EXTENSION):
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
        logger.error(f'File to process does not exist.')
        return False

    logger.info(f"Looking for date string in: {file_path.stem}")
    filedate = extract_date_from_filename(file_path.stem)  # filename without extension
    logger.debug(f"Found Date: {filedate}")
    # this data has more needed details in the filename. example:   Collection Details (A79CD) May 17, 2024 (4).csv
    # the jukebox ID is contained inside the first set of parenthesis and needs to be recovered and matched to the location name.
    touchtunes_device = ID_inside_filename(file_path)

    output_file = Path(f'{ARCHIVE_DIRECTORY_NAME}({touchtunes_device}){OUTPUT_FILE_EXTENSION}')
    logger.debug(f'Output filename: {output_file}')
    # launch the processing function
    try:
        result = aquire_this_data(file_path, filedate, touchtunes_device)
        
        # now generate the output dataframe
        output = process_df(result)

        # processing done, send result to printer
    except Exception as e:
        logger.error(f'Failure processing dataframe: {e}')
        return False
    else:
        if len(result) > 0:
            # save_results_and_print(output_file, result, file_path)
            logger.debug(f'Not yet ready for printing.\n{output}')
        else:
            logger.error(f'No data found to process')
            return False
    # all work complete
    return True


@logger.catch
def aquire_this_data(file_path: Path, date_str, device_id) -> bool:
    # This is the customized procedures used to process this data. Should return a dataframe.
    empty_df = panda.DataFrame()
    
    print(f'{file_path} with embeded date string {date_str} readyness verified.')
    # this csv file is organized with descriptions in column 0 and values in column 1
    """The default download format includes duplicate headers after rotation
        ['1 Credit Jukebox', 'Multi-Credit Jukebox', 'Mobile', 'Karaoke', 'Photobooth', 'Unused credits', 'Cleared credits', 
        'Total Revenue Breakdown', 'Bill', 'Coin', 'Subtotal (Bill + Coin)', 'Linked', 'CC/3rd Party', 'Mobile', 
        'Total Revenue', '1 Credit Jukebox (music)', 'Multi-Credit Jukebox (music)', 'Mobile', 
        'Karaoke service', 'Karaoke BGM', 'Karaoke plays', 'Photobooth print', 'Other fees', 
        'Total Revenues', 'Total fees', 'Total to split', 'Location split', 'Operator split']
    """
    # Read the CSV file. the structure is   descript,value
    #                                       descript,value
    #                                       ...
    # Read the CSV file with no headers
    df = panda.read_csv(file_path, header=None)

    # Set the first column as the index
    df.set_index(0, inplace=True)

    # Rotate the DataFrame 90 degrees to the right
    rotated_df = df.T

    # Reset the index if needed
    rotated_df.reset_index(drop=True, inplace=True)

    logger.debug(f'{rotated_df.columns.to_list()=}')

    # Rename duplicate columns to ensure uniqueness
    new_columns = []
    column_count = {}
    for col in rotated_df.columns:
        if col in column_count:
            column_count[col] += 1
            new_columns.append(f"{col}_{column_count[col]}")
        else:
            column_count[col] = 0
            new_columns.append(col)
    rotated_df.columns = new_columns
    logger.debug(f'{new_columns=}')

    # add the date and device fields
    rotated_df['Device_ID'] = device_id
    rotated_df['Date'] = date_str

    print(f'{rotated_df}')

    print(f'Items: {rotated_df.columns.to_list()}')

    
    # all work complete
    return rotated_df

@logger.catch()
def ID_inside_filename(fn: Path):
    # get the sub-string inside the parenthesis
    file_name_string = fn.name
    parts = file_name_string.split('(')
    if len(parts) > 1:
        subparts = parts[1].split(')')
        if len(subparts) > 1:
            # normalize the ID because the leading zero get dropped by the in-consistant handling by TouchTunes
            if len(subparts[0]) < 6:
                subparts[0] = f'0{subparts[0]}'
            return subparts[0]
    return 'xxxxxx'



@logger.catch()
def process_df(df):
    # Remove un-needed columns
    cols_to_drop = ['1 Credit Jukebox', 'Multi-Credit Jukebox', 'Karaoke', 'Photobooth', 'Unused credits', 'Cleared credits', 'Total Revenue Breakdown', 'Subtotal (Bill + Coin)', 'Linked', 'CC/3rd Party', 'Mobile_1', '1 Credit Jukebox (music)', 'Multi-Credit Jukebox (music)', 'Mobile_2', 'Karaoke service', 'Karaoke BGM', 'Karaoke plays', 'Photobooth print']    # Filter the columns to drop to only those that exist in the DataFrame

    # Check existing columns in the DataFrame
    existing_cols = df.columns.tolist()
    logger.debug(f'{existing_cols=}')

    cols_to_drop_filtered = [col for col in cols_to_drop if col in existing_cols]

    # Drop the filtered columns
    df_dropped = df.drop(columns=cols_to_drop_filtered)
    logger.debug(f'{df_dropped.columns.tolist()=}')
    return df_dropped
