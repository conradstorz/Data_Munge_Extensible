"""Defines functions for common dataframe situations.
    I frequently add notes to a dataframe prior to printing the dataframe.
    The first function simply inserts a given string at the top left of the dataframe.
    Optionally it will allow the string be placed into a given column name.
    Optionally it will allow the string be added after the last row of the given dataframe."""

import pandas as pd
import numpy as np

def insert_string(df: pd.DataFrame, input_string: str, column_name: str = None, position: int = None) -> pd.DataFrame:
    """
    TODO allow any variable to be inserted. default to matching column type pre-existing but allow override option.

        Inserts a string at the top or bottom of a DataFrame. If no column name is specified,
    the string is inserted into the first column of the DataFrame. Raises an 
    exception if the column's data type is not compatible with strings or if
    the column name is not found in the DataFrame.

    TODO default to top and left column unless specified and insert new column if column name specified doesn't exist.
                if new column, default to fill all rows with new value but allow override to specify row
    
    Parameters:
    -----------
    df : pd.DataFrame
        The DataFrame where the string will be inserted.
    input_string : str
        The string to be inserted.
    column_name : str, optional
        The name of the column where the string will be inserted. 
        If not specified, the string will be inserted into the first column.
    position : str, optional
        The position to insert the string. Either 'top' or 'bottom'. Default is 'top'.
        
    Returns:
    --------
    pd.DataFrame
        The modified DataFrame with the string inserted.
    
    Raises:
    -------
    TypeError:
        If the column's data type is not compatible with strings.
    KeyError:
        If the provided column name does not exist in the DataFrame.
    """
    
    # If no position is provided, use the last row
    if position is None:
        position == df.shape[0]  # Number of rows in dataframe
        
    # If no column name is provided, use the first column
    if column_name is None:
        column_name = df.columns[0]

    # Check if the column name exists in the DataFrame
    if column_name not in df.columns:
        raise KeyError(f"The column '{column_name}' was not found in the DataFrame.")
    
    # Check if the column data type is compatible with strings
    if not pd.api.types.is_object_dtype(df[column_name]) and not pd.api.types.is_string_dtype(df[column_name]):
        raise TypeError(f"The column '{column_name}' is not compatible with strings.")
    
    # Create a new row DataFrame with the string in the specified column
    new_row = pd.DataFrame({column_name: [input_string]})

    # Ensure all other columns are filled with NaN for the new row
    for col in df.columns:
        if col not in new_row.columns:
            new_row[col] = np.nan  # Use np.nan for missing values

    # Insert at the top or bottom based on the 'position' argument
    if position == 'top':
        df = pd.concat([new_row, df], ignore_index=True)
    elif position == 'bottom':
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        raise ValueError("Position argument must be either 'top' or 'bottom'.")

    return df

# Example usage (if this script is run directly)
if __name__ == "__main__":
    from io import StringIO

    # CSV formatted data as a string with the first line representing the column names.
    csv_data = """
    A,B,C
    hello,5.1,world
    world,6.1,wide
    friends,4.1,nations
    """

    # Use StringIO to simulate reading from a file
    data = StringIO(csv_data)
    # Create DataFrame
    df = pd.read_csv(data)
    print(df)

    # String to insert
    string_to_insert = "New String"

    # Insert the string at the top
    try:
        df = insert_string(df, string_to_insert, position='top')
    except (KeyError, TypeError, ValueError) as e:
        print(e)

    print(df)

    # Insert the string at the bottom
    try:
        df = insert_string(df, string_to_insert, position='bottom')
    except (KeyError, TypeError, ValueError) as e:
        print(e)

    print(df)

    # Insert the string at the top in column 'C'
    try:
        df = insert_string(df, string_to_insert, column_name='C', position='top')
    except (KeyError, TypeError, ValueError) as e:
        print(e)

    print(df)

    # Insert the string at the bottom in column 'C'
    try:
        df = insert_string(df, string_to_insert, column_name='C', position='bottom')
    except (KeyError, TypeError, ValueError) as e:
        print(e)

    print(df)
