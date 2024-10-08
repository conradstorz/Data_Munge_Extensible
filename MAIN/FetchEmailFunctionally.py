from imap_tools import MailBox, AND
from datetime import datetime, timedelta
import json
from pathlib import Path
from loguru import logger

def fetch_emails_last_24_hours(imap_server, username, password, download_dir, seen_emails_file, ignore_file_types=None):
    """
    Fetch and process emails from the last 24 hours that have not been previously processed.

    :param imap_server: The IMAP server address.
    :type imap_server: str
    :param username: The username to log in to the IMAP server.
    :type username: str
    :param password: The password to log in to the IMAP server.
    :type password: str
    :param download_dir: Directory to save email attachments.
    :type download_dir: str or Path
    :param seen_emails_file: Path to a file where processed email UIDs are saved.
    :type seen_emails_file: str or Path
    :param ignore_file_types: A list of file suffixes to ignore when downloading attachments. Default is None.
    :type ignore_file_types: list
    """
    if ignore_file_types is None:
        ignore_file_types = ["gif"]

    # Ensure the download directory exists
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    # Read the UIDs of previously processed emails
    seen_uids = set()
    if Path(seen_emails_file).exists():
        with open(seen_emails_file, 'r') as f:
            seen_uids = set(f.read().splitlines())

    # Fetch emails from the last 24 hours
    last_24_hours = datetime.now() - timedelta(days=1)
    try:
        with MailBox(imap_server).login(username, password) as mailbox:
            criteria = AND(date_gte=last_24_hours.date())  # Emails in the last 24 hours
            emails = list(mailbox.fetch(criteria))
            logger.info(f"Total emails fetched: {len(emails)}")

            for msg in emails:
                if msg.uid in seen_uids:
                    logger.info(f"Email UID {msg.uid} already processed. Skipping.")
                    continue

                logger.debug(
                    f"Fetched email | Subject: {msg.subject} | Sender: {msg.from_} | Date: {msg.date} | UID: {msg.uid}"
                )
                
                # Process email (implement your logic here)
                # Example: Save email content or attachments
                process_email(msg, download_dir, ignore_file_types)

                # Add the email UID to the seen_uids list and save it
                seen_uids.add(msg.uid)
                with open(seen_emails_file, 'a') as f:
                    f.write(f"{msg.uid}\n")
                    
            logger.debug("Processing completed.")

    except Exception as e:
        logger.error(f"Error occurred while fetching emails: {str(e)}")


def process_email(msg, download_dir, ignore_file_types):
    """
    Process the email message, save its content or attachments if needed.

    :param msg: The email message to process.
    :type msg: imap_tools.EmailMessage
    :param download_dir: Directory to save email attachments.
    :type download_dir: Path
    :param ignore_file_types: List of file suffixes to ignore.
    :type ignore_file_types: list
    """
    logger.info(f"Processing email: {msg.subject}")

    # Save attachments
    for att in msg.attachments:
        if any(att.filename.endswith(ext) for ext in ignore_file_types):
            logger.info(f"Ignoring attachment {att.filename} due to file type restriction.")
            continue
        
        attachment_path = download_dir / att.filename
        with open(attachment_path, 'wb') as f:
            f.write(att.payload)
        logger.info(f"Saved attachment: {attachment_path}")

    # You can extend the logic to save email content or JSON as needed.
    # Example: Save email content as JSON
    email_data = {
        "subject": msg.subject,
        "from": msg.from_,
        "date": msg.date.isoformat(),
        "body": msg.text or msg.html,
    }
    
    email_filename = download_dir / f"{msg.uid}.json"
    with open(email_filename, 'w') as json_file:
        json.dump(email_data, json_file, indent=4)
    
    logger.info(f"Saved email content as: {email_filename}")
