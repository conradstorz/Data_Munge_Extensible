Sure, let's create a Python script that monitors the Downloads folder for new PDF files, extracts data from them, and saves the data to a CSV file. We'll use the `watchdog` library to monitor the folder, `PyPDF2` for extracting text from the PDFs, and the `csv` module to write the data to a CSV file.

### Step-by-Step Plan

1. **Install Required Libraries**:
   - `watchdog` for monitoring the directory.
   - `PyPDF2` for extracting text from PDFs.
   - `pandas` for handling data and writing to CSV.

2. **Monitor the Downloads Folder**:
   - Use `watchdog` to watch for new PDF files in the Downloads folder.

3. **Extract Data from PDFs**:
   - Use `PyPDF2` to read and extract text from the PDFs.

4. **Save Data to a CSV File**:
   - Use the `csv` module or `pandas` to write the extracted data to a CSV file.

### Implementation

Here's the complete script:

```python
import os
import time
import csv
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyPDF2 import PdfFileReader

class Watcher:
    DIRECTORY_TO_WATCH = os.path.expanduser("~/Downloads")

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None
        elif event.src_path.endswith(".pdf"):
            print(f"New PDF file detected: {event.src_path}")
            extract_and_save_data(event.src_path)

def extract_and_save_data(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfFileReader(file)
            text = ""
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                text += page.extract_text()
        
        data = {"file_name": os.path.basename(pdf_path), "content": text}
        save_to_csv(data)
    except Exception as e:
        print(f"Failed to extract data from {pdf_path}: {e}")

def save_to_csv(data):
    csv_file = os.path.expanduser("~/Downloads/extracted_data.csv")
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["file_name", "content"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    print(f"Data saved to {csv_file}")

if __name__ == "__main__":
    w = Watcher()
    w.run()
```

### Explanation

1. **Library Imports**:
   - `os`, `time`, and `csv` are standard Python libraries.
   - `pandas` is used for handling data frames.
   - `watchdog` is used to monitor the directory.
   - `PyPDF2` is used to extract text from PDF files.

2. **Watcher Class**:
   - This class sets up the observer to monitor the Downloads folder.

3. **Handler Class**:
   - This class handles the events triggered by changes in the directory. Specifically, it looks for new PDF files and calls the `extract_and_save_data` function.

4. **extract_and_save_data Function**:
   - This function reads the PDF file, extracts the text, and prepares the data for saving.

5. **save_to_csv Function**:
   - This function appends the extracted data to a CSV file named `extracted_data.csv` in the Downloads folder.

### Installation of Required Libraries

Before running the script, ensure you have installed the necessary libraries:

```sh
pip install watchdog PyPDF2 pandas
```

This script will continuously monitor your Downloads folder for new PDF files, extract their content, and save the data to a CSV file.

Citations:
[1] https://stackoverflow.com/questions/33571641/a-python-script-to-monitor-a-directory-for-new-files
[2] https://www.reddit.com/r/Python/comments/195yfyx/python_library_to_watch_a_directory_for_new_files/
[3] https://stackoverflow.com/questions/4708511/how-to-watch-a-directory-for-changes
[4] https://stackoverflow.com/questions/3984003/how-to-extract-pdf-fields-from-a-filled-out-form-in-python/3985696
[5] https://www.freecodecamp.org/news/extract-data-from-pdf-files-with-python/
[6] https://stackoverflow.com/questions/32667398/best-tool-for-text-extraction-from-pdf-in-python-3-4
[7] https://docs.python.org/3/library/csv.html
[8] https://www.geeksforgeeks.org/working-csv-files-python/
[9] https://gist.github.com/2filip3/bd8d0f26491572c1cce355e9f7e0d366
[10] https://www.reddit.com/r/Python/comments/15b57u8/getting_modules_to_extract_form_field_data_from_a/