import re
from datetime import datetime
from generic_dataframe_functions import is_date_valid
from generic_dataframe_functions import extract_dates
from generic_dataframe_functions import extract_date_from_filename_using_regularExpressions
import pytest


# Test cases using pytest
def test_is_date_valid():
    assert is_date_valid("2024-06-19") == True
    assert is_date_valid("1970-01-01") == True
    assert is_date_valid("2024-08-02") == True
    assert is_date_valid("2024-07-31") == True
    assert is_date_valid("2024-08-04") == True
    assert is_date_valid("2024-02-08") == True
    assert is_date_valid("2024-13-01") == False  # Invalid month
    assert is_date_valid("2024-08-76") == False  # Invalid day
    assert is_date_valid("2024-02-30") == False  # Invalid day
    assert is_date_valid("2024-04-21") == True
    assert is_date_valid("2025-12-31") == True
    assert is_date_valid("2023-10-01") == True
    assert is_date_valid("9999-01-01") == False  # Out of range
    assert is_date_valid("1969-12-31") == False  # Out of range


def test_extract_dates():
    input_strings = {
        "pay_at_machine_log_2024-06-19_to_2024-08-02": ["2024-06-19", "2024-08-02"],
        "ATMActivityReport-2024-08-01-053533AM": ["2024-08-01"],
        "Storz_Amusements_LLC-A13212-2024-08-04-location_sales": ["2024-08-04"],
        "Terminal Status(w_FLOAT)automated 3 - 2024-07-31": ["2024-07-31"],
        "Screenshot_2-8-2024_105738_www.vgtsforindiana.org": ["2024-02-08"],
        "This string has no dates.": ["1970-01-01"],
        "NAC2024 FINAL 4212024a5.PDF this string may be un-parsable": ["1970-01-01"],
        "Collection Details (A79CD) May 17, 2024 (12).csv": ["2024-05-17"],
        "FINAL 4212024a5.PDF this string may be un-parsable": ["1970-01-01"],
    }

    for string in input_strings.keys():

        dates1 = extract_dates(string)
        for indx, date in enumerate(dates1):
            if is_date_valid(date):
                assert date == input_strings[string][indx]

        dates2 = extract_date_from_filename_using_regularExpressions(string)
        for indx, date in enumerate(dates2):
            if is_date_valid(date):
                assert date == input_strings[string][indx]


# To run the tests, use pytest in command line
# pytest -v test_dates.py
