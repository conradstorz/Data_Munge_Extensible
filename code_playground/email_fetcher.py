from imap_tools import MailBox, AND
import json
import re
import unicodedata
from pathlib import Path
from dotenv import dotenv_values

# Email account credentials
username = 'your_email@example.com'
password = 'your_password'
imap_server = 'imap.example.com'  # Replace with your email provider's IMAP server


def sanitize_filename(subject):
    # Normalize the string to NFKD form and encode it to ASCII bytes, ignoring errors
    normalized_subject = unicodedata.normalize('NFKD', subject).encode('ascii', 'ignore').decode('ascii')
    # Define a regex pattern for invalid filename characters, including control characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    safe_subject = re.sub(invalid_chars, '', normalized_subject)  # Remove invalid characters
    safe_subject = re.sub(r'\s+', '_', safe_subject)  # Replace spaces with underscores
    return safe_subject[:255]  # Limit filename length to avoid file system issues

def get_email(imap_server, username, password, mark_as_seen=False):
    """Fetches emails
    """
    # Connect to the mailbox
    with MailBox(imap_server).login(username, password, 'INBOX') as mailbox:
        # Fetch unseen emails
        for msg in mailbox.fetch(AND(seen=False), mark_seen=mark_as_seen):
            email_parts = {
                'subject': msg.subject,
                'from': msg.from_,
                'to': msg.to,
                'date': msg.date_str,
                'body': msg.text or msg.html,
                'attachments': [att.filename for att in msg.attachments]
            }

            # Create a unique filename using the email ID and sanitized subject
            safe_subject = sanitize_filename(msg.subject)
            filename = f"email_{msg.uid}_{safe_subject}.json"

            # Convert the email parts to JSON
            json_output = json.dumps(email_parts, indent=4)

            # Save JSON to a file
            with open(filename, 'w') as json_file:
                json_file.write(json_output)

            print(f"Email data saved to {filename}")



if __name__ == "__main__":

    imap_server = "imap.gmail.com"
    # Email account credentials
    secrets_directory = Path(".env")
    secrets = dotenv_values(secrets_directory)

    username = secrets["EMAIL_USER"]
    password = secrets["EMAIL_PASSWORD"]

    print(get_email(imap_server, username, password, mark_as_seen=True))
