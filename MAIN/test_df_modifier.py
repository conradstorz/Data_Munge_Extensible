# test_df_modifier.py

import pytest
import pandas as pd
from df_modifier import insert_string_at_top


def test_insert_string_at_top_first_column():
    # Test case 1: Inserting string into the first column by default
    df = pd.DataFrame({'A': ["a string", "another string"], 'B': [100, 200]})
    result_df = insert_string_at_top(df, "First Row")
    
    expected_df = pd.DataFrame({'A': ["First Row", 10, 20], 'B': [pd.NA, 100, 200]})
    
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_insert_string_at_top_first_column_when_not_compatible_with_string():
    # Test case 1: Inserting string into the first column by default
    df = pd.DataFrame({'A': [10, 20], 'B': [100, 200]})
    
    # Expecting a TypeError to be raised
    with pytest.raises(TypeError):
        result_df = insert_string_at_top(df, "First Row")


def test_insert_string_at_top_specified_column_when_not_compatible_with_string():
    # Test case 2: Inserting string into a specified column
    df = pd.DataFrame({'A': [10, 20], 'B': [100, 200]})

    # Expecting a TypeError to be raised
    with pytest.raises(TypeError):    
        result_df = insert_string_at_top(df, "Header B", column_name="B")
    

def test_insert_string_invalid_column_name():
    # Test case 3: Invalid column name should raise a KeyError
    df = pd.DataFrame({'A': [10, 20], 'B': [100, 200]})
    
    with pytest.raises(KeyError):
        insert_string_at_top(df, "Header C", column_name="C")


def test_insert_string_incompatible_column_type():
    # Test case 4: Inserting string into a column with incompatible data type should raise a TypeError
    df = pd.DataFrame({'A': [10, 20], 'B': [100.5, 200.6]})
    
    with pytest.raises(TypeError):
        insert_string_at_top(df, "Incompatible String", column_name="B")


def test_insert_string_on_empty_dataframe():
    # Test case: Inserting string into an empty DataFrame
    df = pd.DataFrame(columns=['A', 'B'])
    result_df = insert_string_at_top(df, "New String")

    # Expected DataFrame, ensuring 'B' column is set to 'object'
    expected_df = pd.DataFrame({'A': ["New String"], 'B': [pd.NA]}, dtype="object")
    
    # Ensure both DataFrames have 'object' type for the 'B' column
    result_df['B'] = result_df['B'].astype('object')
    expected_df['B'] = expected_df['B'].astype('object')

    # Ensure both DataFrames use pd.NA consistently
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_insert_string_at_top_with_object_type():
    # Test case 6: Inserting into a column with an object data type (should work)
    df = pd.DataFrame({'A': ['text1', 'text2'], 'B': [100, 200]})
    result_df = insert_string_at_top(df, "Header A")
    
    expected_df = pd.DataFrame({'A': ["Header A", 'text1', 'text2'], 'B': [pd.NA, 100, 200]})
    
    pd.testing.assert_frame_equal(result_df, expected_df)

if __name__ == "__main__":
    pytest.main()
