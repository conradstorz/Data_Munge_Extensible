import re
from datetime import datetime

def is_date_valid(date_str):
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%Y%b%d')
        # Define valid date range
        min_date = datetime(1970, 1, 1)
        max_date = datetime(2170, 1, 1)
        return min_date <= date_obj <= max_date
    except ValueError:
        # If parsing fails, return False
        return False

def extract_dates(strings):
    # Define patterns to match different date formats
    patterns = [
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # YYYY-MM-DD or YYYY_MM_DD
        r'(\d{1,2})-(\d{1,2})-(\d{4})',      # MM-DD-YYYY
        r'(\d{4})(\d{2})(\d{2})',            # YYYYMMDD
        r'(\d{4})([a-zA-Z]{3})(\d{2})',      # YYYYmonDD
        r'([A-Za-z]+) (\d{1,2}), (\d{4})',   # Month DD, YYYY
        r'\b(\d{1,2})(\d{1,2})(\d{4})\b'     # Handle formats like '4212024'
    ]
    
    extracted_dates = {}
    
    for key in strings.keys():
        found_dates = []
        
        # Try each pattern to find dates
        for pattern in patterns:
            matches = re.findall(pattern, key)
            for match in matches:
                if len(match) == 3:
                    try:
                        # Parse and format the date
                        if pattern == patterns[0]:  # YYYY-MM-DD
                            date_str = f"{match[0]}{datetime.strptime(match[1], '%m').strftime('%b').lower()}{match[2]}"
                        elif pattern == patterns[1]:  # MM-DD-YYYY
                            date_str = f"{match[2]}{datetime.strptime(match[0], '%m').strftime('%b').lower()}{match[1]}"
                        elif pattern == patterns[2]:  # YYYYMMDD
                            date_str = f"{match[0]}{datetime.strptime(match[1], '%m').strftime('%b').lower()}{match[2]}"
                        elif pattern == patterns[3]:  # YYYYmonDD
                            date_str = f"{match[0]}{match[1].lower()}{match[2]}"
                        elif pattern == patterns[4]:  # Month DD, YYYY
                            date_str = f"{match[2]}{match[0][:3].lower()}{match[1]}"
                        elif pattern == patterns[5]:  # MMDDYYYY
                            month = match[0].zfill(2)
                            day = match[1].zfill(2)
                            year = match[2]
                            date_str = f"{year}{datetime.strptime(month, '%m').strftime('%b').lower()}{day}"
                        
                        # Validate the date
                        if is_date_valid(date_str):
                            found_dates.append(date_str)
                    except ValueError:
                        continue
        
        # If no valid dates found, use the default
        if not found_dates:
            found_dates = ['1970jan01']
        
        extracted_dates[key] = found_dates
    
    return extracted_dates

# Test the function with the provided dictionary
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

extracted_dates = extract_dates(input_strings)

# Print the extracted dates
for key, dates in extracted_dates.items():
    print(f"{key}: {dates}")
