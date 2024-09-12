import pdfplumber

def pdf_to_text(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

pdf_file = 'lease_Culer_law_office_final_version.pdf'
output_text = pdf_to_text(pdf_file)

if output_text:
    with open('pdfplumber_output_text.txt', 'w') as text_file:
        text_file.write(output_text)
    print("PDF converted to text successfully.")
else:
    print("Failed to convert PDF to text.")

