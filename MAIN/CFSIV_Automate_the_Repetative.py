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


from scripts_manager import ScriptManager
from file_processor import FileProcessor
from directory_watcher import monitor_download_directory
from email_watcher import EmailAttachmentDownloader
from loguru import logger
from pathlib import Path
from dotenv import dotenv_values
import sys

# Remove the default handler
logger.remove()

# Add a handler for the console that logs messages at the INFO level and above
# Add the console handler with colorization enabled
logger.add(sys.stdout, level='INFO', colorize=True, format="<green>{time}</green> <level>{message}</level>")

logger.add("LOGS/file_processing_{time:YYYY-MM-DD}.log", rotation="00:00", retention="9 days")

scripts_directory = Path.cwd() / "MAIN"
directory_to_watch = Path("D:/Users/Conrad/Downloads/")

scripts_manager = ScriptManager(scripts_directory)
file_processor = FileProcessor(scripts_manager)

secrets_directory = scripts_directory / Path(".env")
secrets = dotenv_values(secrets_directory)

email_downloader = EmailAttachmentDownloader(
    email_user=secrets["EMAIL_USER"],
    email_password=secrets["EMAIL_PASSWORD"],
    download_folder=directory_to_watch,
    interval=600,  # Check every 10 minutes
)

# Start the email attachment checking
email_downloader.start()

# This function will run until Keyboard Interrupt is detected
monitor_download_directory(directory_to_watch, file_processor, delay=10)

print("directory watcher ended")
email_downloader.stop()
print("email watcher stopped")
