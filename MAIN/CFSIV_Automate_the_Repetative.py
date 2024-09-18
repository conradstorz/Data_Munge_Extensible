"""CFSIV Data Munge Extensible (w/ChatGPT co-programmer) OOP version 7/19/2024
This script defines a system that allows processing of data from external sources.
Banks, Software Service providers and others provide their own unique access to data they hold.
My need to review or import their data is different for each source.
For example my provider of ATM services generates a daily report that I use to balance my bank accounts.
The data is loaded by a script that I wrote in 2018 and then sent to the printer after being somewhat re-arranged.
Also my bank provides check account transactions but they place the most identifiable information in the memo line
and Quickbooks only looks at the Name field for where to load the transaction and how to classify it. My script for that
swaps these fields and removes extraneous words like 'ckcd', 'ach', 'pos', etc... that add nothing to the transaction.

I have worked with ChatGPT to create a framework for these scripts that will monitor my downloads directory and launch
the proper script for processing the data that is incoming.

"""

from file_processor_and_scripts_manager import ScriptManager, FileProcessor
from directory_watcher import monitor_download_directory
from FetchEmailClass import EmailFetcher
from loguru import logger
from pathlib import Path
from dotenv import dotenv_values
import sys

# setup logging
# Remove the default handler
logger.remove()
# Add a handler for the console that logs messages at the INFO level
# Add the console handler with colorization enabled
logger.add(sys.stdout, level='INFO', colorize=True, format="<green>{time}</green> <level>{message}</level>")
# setup log rotation
logger.add("LOGS/file_processing_{time:YYYY-MM-DD}.log", rotation="00:00", retention="9 days")
logger.info(f'Program Start: {__name__}')

# load data processing functions for various data types
SCRIPTS_DIRECTORY = Path.cwd() / "MAIN"
scripts_manager_instance = ScriptManager(SCRIPTS_DIRECTORY)
scripts_manager_instance.load_scripts()
file_processor_instance = FileProcessor(scripts_manager_instance)

# establish where to look for incoming data
DIRECTORY_TO_WATCH = Path("D:/Users/Conrad/Downloads/")

# load email secrets
SECRETS_DIRECTORY = SCRIPTS_DIRECTORY / Path(".env")
secrets = dotenv_values(SECRETS_DIRECTORY)
IMAP_SERVER = "imap.gmail.com"

# initiate class  (has optional flag 'mark_as_read' that defaults to False)
try:
    email_fetcher = EmailFetcher(IMAP_SERVER, secrets["EMAIL_USER"], secrets["EMAIL_PASSWORD"], interval=180, dld=DIRECTORY_TO_WATCH)
except KeyError as e:
    logger.error(f'Could not initialize email fetcher. KeyError: {str(e)}')

# start fetcher
email_fetcher.start()

# This function will run until Keyboard Interrupt is detected
monitor_download_directory(DIRECTORY_TO_WATCH, file_processor_instance, delay=2)

# begin shutdown
logger.info("directory watcher ended")
email_fetcher.stop()
logger.info("email watcher stopped")
# shutdown complete
sys.exit(0)