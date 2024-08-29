"""Defines common functions for working with dataframes used throughout my code
"""

from loguru import logger
import pandas as panda
from pathlib import Path
from 

@logger.catch()
def data_from_csv(in_f):
    """Import a CSV file into a datframe"""
    empty_df = panda.DataFrame()
    # load csv file into dataframe
    logger.debug(f"Reading CSV data using Pandas on file {in_f}")
    try:
        df = panda.read_csv(in_f)
    except Exception as e:
        logger.error(f"Problem using pandas: {e}")
        return empty_df
    else:
        logger.debug(f"imported file processed by pandas okay.")
        DF_LAST_ROW = len(df)
        logger.info(f"file imported into dataframe with {DF_LAST_ROW} rows.")
        return df


@logger.catch()
def load_csv_with_optional_headers(in_f: str, headers="") -> panda.DataFrame:
    # Set headers to empty list if it's an empty string
    if headers == "":
        headers = []
    else:
        if not isinstance(headers, list):
            logger.error("optional headers field must be a list of strings")
            return panda.DataFrame()  # Return empty DataFrame

    empty_df = panda.DataFrame()
    # Load CSV file into DataFrame
    try:
        df = panda.read_csv(in_f, header=None if not headers else 0)
    except Exception as e:
        logger.error(f"Problem using pandas: {e}")
        return empty_df

    # Handle possible header length mismatch
    if headers:
        num_columns = df.shape[1]
        if len(headers) < num_columns:
            logger.warning(
                f"Number of headers ({len(headers)}) is less than number of columns ({num_columns}). Numbering missing headers."
            )
            headers.extend(
                [f"Missing_Header_{i+1}" for i in range(len(headers), num_columns)]
            )  # Number missing headers
        elif len(headers) > num_columns:
            logger.warning(
                f"Number of headers ({len(headers)}) exceeds number of columns ({num_columns}). Truncating to match."
            )
            headers = headers[:num_columns]  # Truncate headers to match column count
        df.columns = headers

    return df


@logger.catch()
def dataframe_contains(df, list):
    """Examine dataframe for existance of columns named in list
    and return list of columns from list that do exist.
    """
    column_list = df.columns.tolist()
    matched_columns = [col for col in list if col in column_list]
    return matched_columns


@logger.catch()
def de_duplicate_header_names(df):
    # Rename duplicate columns to ensure uniqueness
    new_columns = []
    column_count = {}
    for col in df.columns:
        if col in column_count:
            column_count[col] += 1
            new_columns.append(f"{col}_{column_count[col]}")
        else:
            column_count[col] = 0
            new_columns.append(col)
    df.columns = new_columns
    logger.debug(f"{new_columns=}")
    return df


@logger.catch()
def save_results_and_print(output_file, result, file_path):
    # This wrapper function is to maintain compatabilitiy with existing code
    save_results(output_file, result, file_path)


@logger.catch()
def save_results(outfile: Path, frame, input_filename: Path) -> bool:
    """
    Save results to a file and manage file movement.

    Args:
        outfile (Path): Path to the output file.
        frame (DataFrame): Data to be saved.
        input_filename (Path): Original input file name.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if len(frame) > 0:
            logger.info(f"Sending Float Report to file/print...")
            convert_dataframe_to_excel_with_formatting_and_save(outfile, frame)
        else:
            logger.error(f"Dataframe {input_filename} is empty.")
            return False
    except Exception as e:
        logger.error(f"Failure processing dataframe: {e}")
        return False

    if input_filename:
        move_original_file(input_filename, outfile)

    return True


def send_dataframe_to_file(outfile: Path, frame):
    # Save the dataframe to a file
    frame.to_csv(outfile, index=False)
    logger.info(f"Dataframe saved to {outfile}")


def print_dataframe(frame):
    # Print the dataframe
    logger.info(frame)
    logger.info("Dataframe printed to console")


def Send_dataframe_to_file_and_print(outfile: Path, frame):
    """
    Save the dataframe to a file and print it.

    Args:
        outfile (Path): Path to the output file.
        frame (DataFrame): Data to be saved and printed.
    """
    convert_dataframe_to_excel_with_formatting_and_save(outfile, frame)
    send_dataframe_to_file(outfile, frame)
    print_dataframe(frame)

