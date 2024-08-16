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

TODO add a function that monitors my email and auto-downloads attachments for possible processing
"""


if __name__ == "__main__":
    from scripts_manager import ScriptManager
    from file_processor import FileProcessor
    from directory_watcher import DirectoryWatcher
    from email_watcher import EmailAttachmentDownloader
    from loguru import logger
    from pathlib import Path
    from dotenv import dotenv_values

    secrets = dotenv_values(".env")

    logger.add("file_processing.log", rotation="10 MB")

    scripts_directory = Path.cwd() / "MAIN"
    directory_to_watch = Path("D:/Users/Conrad/Downloads/")

    scripts_manager = ScriptManager(scripts_directory)
    file_processor = FileProcessor(scripts_manager)
    directory_watcher = DirectoryWatcher(directory_to_watch, file_processor)


    email_downloader = EmailAttachmentDownloader(
        email_user=secrets['EMAIL_USER'],
        email_password=secrets['EMAIL_PASSWORD'],
        download_folder=directory_to_watch,
        interval=600  # Check every 10 minutes
    )

    # Start the email attachment checking
    email_downloader.start()


    try:
        directory_watcher.run()
    except Exception as e:
        logger.error(f"Error in directory watcher: {e}")
