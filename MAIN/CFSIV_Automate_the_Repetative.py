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
# Add a handler for the console that logs messages at the INFO level and above
# Add the console handler with colorization enabled
logger.add(sys.stdout, level='INFO', colorize=True, format="<green>{time}</green> <level>{message}</level>")
logger.add("LOGS/file_processing_{time:YYYY-MM-DD}.log", rotation="00:00", retention="9 days")

# load data processing functions
scripts_directory = Path.cwd() / "MAIN"
directory_to_watch = Path("D:/Users/Conrad/Downloads/")
scripts_manager = ScriptManager(scripts_directory)
scripts_manager.load_scripts()
file_processor = FileProcessor(scripts_manager)
file_processor.process(directory_to_watch)

# load email secrets
secrets_directory = scripts_directory / Path(".env")
secrets = dotenv_values(secrets_directory)
imap_server = "imap.gmail.com"
# initiate class  (has optional flag 'mark_as_read' that defaults to False)
email_fetcher = EmailFetcher(imap_server, secrets["EMAIL_USER"], secrets["EMAIL_PASSWORD"], interval=600)
# start fetcher
email_fetcher.run()

# This function will run until Keyboard Interrupt is detected
monitor_download_directory(directory_to_watch, file_processor, delay=10)

print("directory watcher ended")
email_fetcher.stop()
print("email watcher stopped")
