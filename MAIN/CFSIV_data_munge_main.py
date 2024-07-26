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
from pathlib import Path

if __name__ == "__main__":
    from scripts_manager import ScriptManager
    from file_processor import FileProcessor
    from directory_watcher import DirectoryWatcher
    from loguru import logger

    logger.add("file_processing.log", rotation="10 MB")

    scripts_directory = Path.cwd() / "MAIN"
    directory_to_watch = Path("D:/Users/Conrad/Downloads/")

    scripts_manager = ScriptManager(scripts_directory)
    file_processor = FileProcessor(scripts_manager)
    directory_watcher = DirectoryWatcher(directory_to_watch, file_processor)

    directory_watcher.run()