import re
from datetime import datetime

def extract_and_order_dates(log_string):
    # Regular expression patterns for different date formats
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # M-D-YYYY or D-M-YYYY
        r'\b\d{4}_\d{2}_\d{2}\b',  # YYYY_MM_DD
        r'\b\d{2}_\d{2}_\d{4}\b',  # DD_MM_YYYY
        r'\b\d{8}\b',              # YYYYMMDD or DDMMYYYY
        r'\b\d{1,2}\d{1,2}\d{4}\b'   # MDDYYYY or MMDDYYYY
    ]

    dates = set()  # Use a set to avoid duplicates

    # Extract dates using regex patterns
    for pattern in date_patterns:
        found_dates = re.findall(pattern, log_string)
        dates.update(found_dates)

    # Check if any dates are found
    if not dates:
        return ['1970-01-01']

    date_objects = []

    # Convert string dates to datetime objects
    for date in dates:
        try:
            # Attempt parsing based on the expected formats
            if '-' in date and len(date.split('-')[0]) == 4:
                date_obj = datetime.strptime(date, '%Y-%m-%d')  # YYYY-MM-DD
            elif '-' in date:
                date_obj = datetime.strptime(date, '%m-%d-%Y')  # M-D-YYYY or D-M-YYYY
            elif '_' in date and len(date.split('_')[0]) == 4:
                date_obj = datetime.strptime(date, '%Y_%m_%d')  # YYYY_MM_DD
            elif '_' in date:
                date_obj = datetime.strptime(date, '%d_%m_%Y')  # DD_MM_YYYY
            elif len(date) == 8 and date.isdigit():
                try:
                    date_obj = datetime.strptime(date, '%Y%m%d')  # YYYYMMDD
                except ValueError:
                    date_obj = datetime.strptime(date, '%d%m%Y')  # DDMMYYYY
            elif len(date) == 8:
                date_obj = datetime.strptime(date, '%m%d%Y')  # MDDYYYY or MMDDYYYY
            date_objects.append(date_obj)
        except ValueError:
            continue

    # Sort dates in ascending order
    sorted_dates = sorted(date_objects)

    # Convert back to string format in the desired output format
    return [date.strftime('%Y-%m-%d') for date in sorted_dates]

# Example test cases we are only dealing with dates at this point not time stamps
log_strings = {
    'pay_at_machine_log_2024_06_19_to_2024_08_02': ['2024jun19', '2024aug02'],
    'ATMActivityReport-20240801-053533AM': ['2024aug01'],
    'Storz_Amusements_LLC-A13212-2024-08-04-location_sales': ['2024aug04'],
    'Terminal Status(w_FLOAT)automated 3 - 20240731': ['2024jul31'],
    'Screenshot_2-8-2024_105738_www.vgtsforindiana.org': ['2024feb08'],
    'This string has no dates.': ['1970jan01'],
    'NAC2024 FINAL 4212024a5.PDF this string may be un-parsable': ['2024apr21'],
    'Collection Details (A79CD) May 17, 2024 (12).csv': ['2024may17']
}
"""
import re

string = 'Collection Details (A79CD) May 17, 2024 (4)'
date_pattern = r'\b([A-Za-z]+ \d{1,2}, \d{4})\b'
date_match = re.search(date_pattern, string)
extracted_date = date_match.group(0) if date_match else None
print(extracted_date)
"""

for log in log_strings.keys():
    result = extract_and_order_dates(log)
    # TODO test for correct result
    print(f'{result=} should be {log_strings[log]}')