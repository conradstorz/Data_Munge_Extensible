I understand you want the output CSV file to have a unique name that identifies the source PDF file. Let's modify our script to incorporate this requirement. We'll use the original PDF filename as a base and add a timestamp to ensure uniqueness. Here's how we can update the `save_to_csv` function:

```python
import os
import csv
from datetime import datetime

def save_to_csv(data, pdf_path):
    # Extract the original PDF filename without SUFFIX
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a unique CSV filename
    csv_filename = f"{pdf_filename}_{timestamp}.csv"
    csv_file = os.path.join(os.path.expanduser("~/Downloads"), csv_filename)
    
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["file_name", "content"])
        writer.writeheader()
        writer.writerow(data)
    print(f"Data saved to {csv_file}")
```

This updated function does the following:

1. It extracts the original PDF filename without the SUFFIX using `os.path.splitext()` and `os.path.basename()`.

2. It creates a timestamp using the current date and time, formatted as "YYYYMMDD_HHMMSS".

3. It combines the original PDF filename and the timestamp to create a unique CSV filename.

4. It saves the data to this uniquely named CSV file in the Downloads folder.

Now, when you call this function, it will create a CSV file with a name that includes both the original PDF filename and a timestamp, ensuring uniqueness and traceability back to the source PDF.

For example, if the original PDF was named "report.pdf", the resulting CSV might be named something like "report_20240715_143022.csv".

To use this in your main script, you would call it like this:

```python
def extract_and_save_data(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfFileReader(file)
            text = ""
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                text += page.extract_text()
        
        data = {"file_name": os.path.basename(pdf_path), "content": text}
        save_to_csv(data, pdf_path)
    except Exception as e:
        print(f"Failed to extract data from {pdf_path}: {e}")
```

This approach ensures that each CSV file has a unique name that directly relates to its source PDF file, making it easy to track and manage your extracted data.

Citations:
[1] https://stackoverflow.com/questions/2961509/python-how-to-create-a-unique-file-name
[2] https://www.reddit.com/r/learnpython/comments/vk2bes/generate_a_unique_id_as_a_file_name/
[3] https://www.youtube.com/watch?v=UKoUiZC0bL8
[4] https://blog.finxter.com/5-best-ways-to-program-to-make-file-names-unique-using-python/
[5] https://pypi.org/project/unique-names-generator/
[6] https://www.toolify.ai/ai-news/create-unique-file-names-in-python-71792
[7] https://mysticmind.dev/how-to-create-unique-file-names-in-bash-shell
[8] https://www.tutorialspoint.com/program-to-make-file-names-unique-using-python