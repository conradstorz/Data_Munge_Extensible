import re
from datetime import datetime

def extract_and_order_dates(log_string):
    # Extract dates using regex for both YYYY_MM_DD, YYYYMMDD, and YYYY-MM-DD formats
    pattern = r'\d{4}_\d{2}_\d{2}|\d{8}|\d{4}-\d{2}-\d{2}'
    dates = re.findall(pattern, log_string)
    
    # Convert string dates to datetime objects
    date_objects = []
    for date in dates:
        if '_' in date:  # format YYYY_MM_DD
            date_obj = datetime.strptime(date, '%Y_%m_%d')
        elif '-' in date:  # format YYYY-MM-DD
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:  # format YYYYMMDD
            date_obj = datetime.strptime(date, '%Y%m%d')
        date_objects.append(date_obj)
    
    # Sort dates in ascending order
    sorted_dates = sorted(date_objects)
    
    # Convert back to string format in the desired output format
    return [date.strftime('%Y-%m-%d') for date in sorted_dates]

# Test with various log strings
log_strings = [
    'pay_at_machine_log_2024_06_19_to_2024_08_02',
    'ATMActivityReport-20240801-053533AM',
    'Storz_Amusements_LLC-A13212-2024-08-04-location_sales',
    'Terminal Status(w_FLOAT)automated 3 - 20240731',
    'Screenshot_2-8-2024_105738_www.vgtsforindiana.org',
    'nodemcu3a'
]

for log in log_strings:
    print(extract_and_order_dates(log))