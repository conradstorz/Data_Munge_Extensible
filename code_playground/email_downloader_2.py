import imaplib
import email
import json
from email.header import decode_header
import re
import unicodedata
from dotenv import dotenv_values
from pathlib import Path

def sanitize_filename(subject):
    # Normalize the string to NFKD form and encode it to ASCII bytes, ignoring errors
    normalized_subject = unicodedata.normalize('NFKD', subject).encode('ascii', 'ignore').decode('ascii')
    # Define a regex pattern for invalid filename characters, including control characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    safe_subject = re.sub(invalid_chars, '', normalized_subject)  # Remove invalid characters
    safe_subject = re.sub(r'\s+', '_', safe_subject)  # Replace spaces with underscores
    return safe_subject[:255]  # Limit filename length to avoid file system issues


def get_a_new_gmail(username, password, mark_as_read=False):
    """Get the first new email and optionally mark it read.
    """
    # Connect to the server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")  # Replace with your email provider's IMAP server
    mail.login(username, password)

    # Select the mailbox you want to check (e.g., inbox)
    mail.select("inbox")

    # Search for unseen emails
    _status, messages = mail.search(None, 'UNSEEN')

    # Convert the result to a list of email IDs
    email_ids = messages[0].split()

    # Check if there are any new emails
    if email_ids:
        # Fetch the first unseen email
        for email_id in email_ids:
            # Fetch the email
            if mark_as_read == False:
                status, msg_data = mail.fetch(email_id, '(BODY.PEEK[])')  # Do not change message status
            else:
                status, msg_data = mail.fetch(email_id, '(RFC822)')  # Status will be changed

            # Parse the email content
            email_parts = {}
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # Decode the subject if it's in bytes
                        subject = subject.decode(encoding if encoding else 'utf-8')
                    email_parts['subject'] = subject
                    email_parts['from'] = msg['From']
                    email_parts['to'] = msg['To']
                    email_parts['date'] = msg['Date']

                    # Email body and attachments
                    email_parts['body'] = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            # Process attachments
                            if "attachment" in content_disposition:
                                filename = part.get_filename()
                                if filename:
                                    email_parts['body'].append({"attachment": filename})
                            elif content_type == 'text/plain':
                                email_parts['body'].append({"body": part.get_payload(decode=True).decode()})
                    else:
                        # If the email is not multipart
                        content_type = msg.get_content_type()
                        if content_type == 'text/plain':
                            email_parts['body'].append({"body": msg.get_payload(decode=True).decode()})

            # Create a unique filename using the email ID
            safe_subject = sanitize_filename(subject)
            filename = f"email_{email_id.decode()}_{safe_subject}.json"

            # Convert the email parts to JSON
            json_output = json.dumps(email_parts, indent=4)

            # Save JSON to a file
            with open(filename, 'w') as json_file:
                json_file.write(json_output)

            return filename

    else:
        return "No email"

    # Logout from the server
    mail.logout()


if __name__ == "__main__":

    # Email account credentials
    secrets_directory = Path(".env")
    secrets = dotenv_values(secrets_directory)

    username = secrets["EMAIL_USER"]
    password = secrets["EMAIL_PASSWORD"]

    print(get_a_new_gmail(username, password, mark_as_read=True))
