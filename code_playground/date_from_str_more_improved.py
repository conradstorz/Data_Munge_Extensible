import re
from datetime import datetime
import pytest


# Test cases using pytest
def test_is_date_valid():
    assert is_date_valid('2024jun19') == True
    assert is_date_valid('1970jan01') == True
    assert is_date_valid('2024aug02') == True
    assert is_date_valid('20240731') == True
    assert is_date_valid('20240804') == True
    assert is_date_valid('2024feb08') == True
    assert is_date_valid('20241301') == False
    assert is_date_valid('20240876') == False
    assert is_date_valid('2024feb30') == False    
    assert is_date_valid('2024apr21') == True
    assert is_date_valid('2025dec31') == True
    assert is_date_valid('2023oct01') == True
    assert is_date_valid('9999jan01') == False  # Out of range
    assert is_date_valid('1969dec31') == False  # Out of range

def test_extract_dates():
    input_strings = {
        'pay_at_machine_log_2024_06_19_to_2024_08_02': ['2024jun19', '2024aug02'],
        'ATMActivityReport-20240801-053533AM': ['2024aug01'],
        'Storz_Amusements_LLC-A13212-2024-08-04-location_sales': ['2024aug04'],
        'Terminal Status(w_FLOAT)automated 3 - 20240731': ['2024jul31'],
        'Screenshot_2-8-2024_105738_www.vgtsforindiana.org': ['2024feb08'],
        'This string has no dates.': ['1970jan01'],
        'NAC2024 FINAL 4212024a5.PDF this string may be un-parsable': ['2024apr21'],
        'Collection Details (A79CD) May 17, 2024 (12).csv': ['2024may17'],
        'FINAL 4212024a5.PDF this string may be un-parsable': ['2024apr21']
    }
    expected_output = {
        'pay_at_machine_log_2024_06_19_to_2024_08_02': ['2024jun19', '2024aug02'],
        'ATMActivityReport-20240801-053533AM': ['2024aug01'],
        'Storz_Amusements_LLC-A13212-2024-08-04-location_sales': ['2024aug04'],
        'Terminal Status(w_FLOAT)automated 3 - 20240731': ['2024jul31'],
        'Screenshot_2-8-2024_105738_www.vgtsforindiana.org': ['2024feb08'],
        'This string has no dates.': ['1970jan01'],
        'NAC2024 FINAL 4212024a5.PDF this string may be un-parsable': ['2024apr21'],
        'Collection Details (A79CD) May 17, 2024 (12).csv': ['2024may17'],
        'FINAL 4212024a5.PDF this string may be un-parsable': ['2024apr21']
    }

    extracted_dates = extract_dates(input_strings)
    assert extracted_dates == expected_output

# To run the tests, use pytest in command line
# pytest -v test_dates.py
