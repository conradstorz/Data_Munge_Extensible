from pdf2image import convert_from_path
import pytesseract
import pandas as pd

def pdf_to_csv(pdf_path, csv_path):
    # Convert PDF to images
    images = convert_from_path(pdf_path)
    
    data = []
    
    for image in images:
        # Use OCR to extract text from each image
        text = pytesseract.image_to_string(image)
        lines = text.split('\n')
        
        for line in lines:
            # Split lines into words based on spaces
            data.append(line.split())

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Save to CSV
    df.to_csv(csv_path, index=False, header=False)

# Example usage
pdf_to_csv('touchtunes_collection_history.pdf', 'output_tt_data.csv')
