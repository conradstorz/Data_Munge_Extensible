""" Version 2024.3 qbo_updater / Modify Quickbooks bank downloads to improve importing accuracy.
"""

from loguru import logger
from pathlib import Path
import re
import generic_pathlib_file_methods as plfh

QBO_MODIFIED_DIRECTORY = Path("D:/Users/Conrad/Documents/")

# standardized declaration for CFSIV_Data_Munge_Extensible project
INPUT_DATA_FILE_EXTENSION = ".qbo"
FILENAME_STRINGS_TO_MATCH = ["Export-", "dummy place holder"]


class FileMatcher:
    """
    Declaration for matching files to the script.

    :param filename: Name of the file to match
    :type filename: str
    :return: True if the script matches the file, False otherwise
    :rtype: bool
    """

    @logger.catch()
    def matches(self, filename: Path) -> bool:
        """
        Determines if the given filename matches the specified patterns and extension.

        :param filename: The Path object representing the file to check.
        :type filename: Path
        :return: True if the file matches, False otherwise.
        :rtype: bool
        """
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(INPUT_DATA_FILE_EXTENSION):
            return True  # match found
        else:
            return False  # no match

    def get_filename_strings_to_match(self):
        """
        Returns the list of filename strings to match.

        :return: A list of filename strings to match.
        :rtype: list
        """
        return FILENAME_STRINGS_TO_MATCH


# activate declaration
declaration = FileMatcher()


@logger.catch
def data_handler_process(file_path: Path) -> bool:
    """
    Processes the data file specified by the file path.

    This function checks if the file exists, processes its contents,
    and moves the file to the appropriate history folder.

    :param file_path: The Path object representing the file to process.
    :type file_path: Path
    :return: True if the file was successfully processed, False otherwise.
    :rtype: bool
    """
    if not file_path.exists:
        logger.error(f"File to process does not exist.")
        return False
    else:
        # process file
        original_records_list = read_base_file(file_path)
        if not len(original_records_list) > 0:
            logger.error(f"File returned no records.")
            return False
        # we have a file, try to process
        logger.info(f"file found to process: {file_path.name}")
        modify_QBO(original_records_list)
        # work finished remove original file from download directory
        new_file_path = file_path.parent / "QBO_file_history" / file_path.name
        # move the file
        plfh.move_file_with_check(file_path, new_file_path, exist_ok=True)
    # all work complete
    return True


@logger.catch
def modify_QBO(QBO_records_list):
    """Take a list of strings from a QBO file format and improve transaction names and memos.
    Wesbanco Bank places all useful info into the memo line. Quickbooks processes transactions based on the names.
    Wesbanco places verbose human readable descriptions in the memo line and a simple transaction number in the name.
    Let's swap those to help quickbooks process the transactions and categorize them.
    Quickbooks limits names of transactions to 32 characters so let's remove the verbose language from the original memos.
    """
    modified_qbo, file_date, acct_number = process_qbo_lines(QBO_records_list)
    # Attempt to write results to cleanfile
    fname = "".join([file_date, "_", acct_number, INPUT_DATA_FILE_EXTENSION])
    logger.debug(f"Attempting to output modified lines to file name: {fname}")
    clean_output_file = Path(QBO_MODIFIED_DIRECTORY, fname)
    try:
        with open(clean_output_file, "w") as f:
            f.writelines(modified_qbo)
    except Exception as e:
        logger.error(f"Error in writing {clean_output_file}")
        logger.warning(str(e))
        return False

    logger.info(f"File {clean_output_file} contents written successfully.")
    return True


@logger.catch
def preprocess_memo(memo):
    # Remove specified bad text patterns
    BAD_TEXT = [
        r"DEBIT +\d{4}",  # TODO should this be removed as unneccessary?
        "CKCD ",  # the space included here ensures that this string is not part of a bigger word
        "AC-",  # no space here allows this substring to be removed from a string
        "POS DB ",
        "POS ",  # 'pos' won't be removed from words like 'position'
        "-ONLINE ",
        "-ACH ",
        "DEBIT ",
        "CREDIT ",
        "ACH ",  # possibly i need to consider how these strings are handled by the cleaning routine.
        "MISCELLANEOUS ",  # 'ach ' would probably match 'reach ' and result in 're'
        "PREAUTHORIZED ",
        "PURCHASE ",
        "TERMINAL ",
        "ATM ",
        "BOOK ",
        "REF ",
        "BillPay ",
        "Insurance ",
        "SEWER PMT ",
        "FREIGHT TOOLS ",
        "ENER ",
        "FUNDS ",
        "ANYWHERE ",
        "ACHTRANS ",
        "NAYAX REIM ",
        "EFTRANSACT ",
        "LOAN PAYMENT ",
        "TECHNOL ",
        "MERCHANT ",
        "AUTOMATIC ",
        "TRANSFER ",
    ]
    logger.debug(f"Original memo line:{memo}")
    for bad_text in BAD_TEXT:
        if re.match(r".*\d{4}.*", bad_text):  # Check if the bad text is a regex pattern
            memo = re.sub(bad_text, "", memo)
        else:
            memo = memo.replace(bad_text, "")
    # Shortening common phrases (if any remain)
    memo = memo.replace("BILL PAYMT", "BillPay").strip()
    # Further cleanup to remove extra spaces and standardize spacing
    memo = re.sub(" +", " ", memo).strip()
    logger.debug(f"Cleaned memo:{memo}")
    return memo


@logger.catch
def truncate_name(name, max_length=32):
    """
    Truncate the name value to ensure it does not exceed QuickBooks' limit.
    
    Parameters:
    - name (str): The name to be truncated.
    - max_length (int, optional): The maximum allowed length. Defaults to 32.
    
    Returns:
    - str: The truncated name.
    
    Raises:
    - ValueError: If 'name' is not a string.
    """
    if not isinstance(name, str):
        raise ValueError("The 'name' must be a string.")
    return name[:max_length]



@logger.catch
def extract_transaction_details(transaction_lines):
    """Extract details from transaction lines into a dictionary of tag:value."""
    transaction_details = {}
    
    for line in transaction_lines:
        line = line.strip()
        
        if not line:
            continue  # Skip empty lines
        
        # Split the line at the first occurrence of ">" to separate the tag from its value
        parts = line.split(">", 1)
        
        if len(parts) == 2 and parts[0].startswith("<"):
            tag = parts[0][1:].strip()  # Remove the opening "<" from the tag
            value = parts[1].strip()  # Strip any leading/trailing whitespace from value
            
            if tag in transaction_details:
                logger.warning(f"Duplicate tag '{tag}' found. Overwriting previous value.")
            
            transaction_details[tag] = value
    
    logger.debug(f"Extracted transaction details: {transaction_details}")
    return transaction_details



@logger.catch
def process_transaction(transaction_lines):
    """Process individual transactions, ensuring memo presence, checking name and memo equality,
    and reformatting back into a list of lines."""
    transaction_details = extract_transaction_details(transaction_lines)
    # Ensure there's a memo tag, add a default one if necessary
    if "MEMO" not in transaction_details:
        transaction_details["MEMO"] = "No Memo"
    else:
        # memo needs to be stripped of bad text and truncated
        transaction_details["MEMO"] = truncate_name(
            preprocess_memo(transaction_details["MEMO"])
        )
    logger.debug(transaction_details)
    # Check for equality of name and memo
    if "NAME" not in transaction_details:
        transaction_details["NAME"] = "No Name"
    name = transaction_details["NAME"]
    memo = transaction_details["MEMO"]
    if name == memo == "CHECK PAID":
        # Use checknum for name and refnum for memo if available
        checknum = transaction_details.get("CHECKNUM", "No CheckNum")
        refnum = transaction_details.get("REFNUM", "No RefNum")
        transaction_details["NAME"] = checknum
        transaction_details["MEMO"] = refnum
    else:
        # name and memo are different so we need to swap their values using the power of tuple unpacking
        transaction_details["NAME"], transaction_details["MEMO"] = transaction_details[
            "MEMO"
        ], transaction_details.get("NAME", "No Name")
    logger.debug(transaction_details)
    # Convert transaction_details back into a list of lines
    processed_lines = []
    for tag, value in transaction_details.items():
        line = f"<{tag}>{value}\n"
        processed_lines.append(line)
    return processed_lines


@logger.catch
def process_qbo_lines(lines):
    qbo_file_date = "19700101"  # default value incase no date found
    account_number = "42"  # default
    modified_lines = []  # Stores the modified lines of the entire file
    transaction_lines = []  # Temporarily stores lines of the current transaction
    processing_transaction = (
        False  # Flag to indicate if we're within a transaction block
    )
    xacts_found = 0  # initialize counter of transactions found
    for line in lines:
        line_stripped = line.strip()
        # Process header lines to extract date and account number
        if line_stripped.startswith("<DTEND>"):
            qbo_file_date = line_stripped.replace("<DTEND>", "")
        elif line_stripped.startswith("<ACCTID>"):
            account_number = line_stripped.replace("<ACCTID>", "")
        if line_stripped.startswith("<STMTTRN>"):
            processing_transaction = True  # Mark the start of a transaction
            xacts_found += 1  # increment counter
            transaction_lines = [line]  # Start a new transaction block
        elif line_stripped.startswith("</STMTTRN>"):
            # End of transaction found
            transaction_lines.append(line)  # append the line
            processing_transaction = (
                False  # Reset the flag as the transaction block ends
            )
            modified_transaction_lines = process_transaction(
                transaction_lines
            )  # Process the collected lines of the transaction
            modified_lines.extend(
                modified_transaction_lines
            )  # Add processed lines to the output
        elif processing_transaction:
            # If we are within a transaction, keep collecting its lines
            transaction_lines.append(line)
        else:
            # Lines not part of a transaction are added directly to the output
            modified_lines.append(line)
    logger.debug(f"{xacts_found} transactions found.")
    logger.debug(modified_lines)  # TODO make this output more log friendly
    return modified_lines, qbo_file_date, account_number


@logger.catch

def read_base_file(input_file: Path):
    """
    Reads the contents of the specified file and returns a list of its lines.

    This function attempts to open the file at the given path and read its contents.
    If the file is successfully read, it returns a list of lines. If an error occurs,
    it logs the error and returns an empty list.

    :param input_file: The path to the file to be read (as a `Path` object).
    :type input_file: Path
    :return: A list containing the lines of the file. Returns an empty list if an error occurs.
    :rtype: list[str]
    
    :raises FileNotFoundError: If the file does not exist.
    :raises PermissionError: If there are insufficient permissions to read the file.
    :raises Exception: For any other exceptions encountered during the file read process.

    :example:

    >>> from pathlib import Path
    >>> file_path = Path("example.txt")
    >>> lines = read_base_file(file_path)
    >>> print(lines)
    ['Line 1', 'Line 2', 'Line 3']

    """
    logger.debug(f"Attempting to open input file {input_file.name}")
    try:
        # Use Path's read_text method to read the entire file
        file_contents = input_file.read_text().splitlines()
    except FileNotFoundError:
        logger.error(f"File not found: {input_file.name}")
        file_contents = []
    except PermissionError:
        logger.error(f"Permission denied: {input_file.name}")
        file_contents = []
    except Exception as e:
        logger.error(f"Error reading {input_file.name}: {str(e)}")
        file_contents = []

    if file_contents:
        logger.debug(f"File contents read successfully. {len(file_contents)} lines.")
    return file_contents

