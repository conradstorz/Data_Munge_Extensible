from imap_tools import MailBox, AND
import json
from pathlib import Path
from loguru import logger
from generic_pathlib_file_methods import sanitize_filename
from datetime import datetime


def fetch_one_email(imap_server, username, password, mark_as_seen=False, ignore_file_types=None, download_dir=""):
    """
    A function to fetch one new email from an IMAP server and process it.
    
    :param imap_server: The IMAP server address.
    :type imap_server: str
    :param username: The username to log in to the IMAP server.
    :type username: str
    :param password: The password to log in to the IMAP server.
    :type password: str
    :param mark_as_seen: Whether to mark emails as seen after fetching. Default is False.
    :type mark_as_seen: bool
    :param ignore_file_types: A list of file suffixes to ignore when downloading attachments.
    :type ignore_file_types: list
    :param dld: Directory to download the attachments
    :type dld: str
    :return: A dictionary with email content or None if no new email is found.
    :rtype: dict or None
    """

    # Connect to the mailbox and fetch one new email
    logger.info('Checking eMail provider...')
    # self.username = 'crash'  # introduce a code exception
    with MailBox(imap_server).login(username, password) as mailbox:
        # Fetch all emails matching the criteria
        messages = mailbox.fetch(AND(seen=False), mark_seen=mark_as_seen, limit=1)
        logger.info(f"Total emails fetched: {len(messages)}")       

        for msg in messages:
            # Create a dictionary for storing email details
            email_data = {
                "from": msg.from_,
                "to": msg.to,
                "subject": msg.subject,
                "date": msg.date.isoformat(),
                "text": msg.text,
                "html": msg.html,
                "attachments": []
            }
            
            # Process attachments
            for att in msg.attachments:
                if not any(att.filename.lower().endswith(ftype) for ftype in ignore_file_types):
                    sanitized_name = sanitize_filename(att.filename)
                    attachment_path = download_dir / sanitized_name
                    with open(attachment_path, "wb") as f:
                        f.write(att.payload)
                    email_data["attachments"].append({
                        "filename": sanitized_name,
                        "content_type": att.content_type,
                        "size": att.size,
                        "path": str(attachment_path)
                    })
            
            # Save email content to a JSON file
            email_file = download_dir / f"{sanitize_filename(msg.subject)}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            with open(email_file, "w") as f:
                json.dump(email_data, f, indent=4)
            
            logger.info(f"Email from {msg.from_} processed and saved to {email_file}")
            
            # Return the processed email data
            return email_data
    
    # If no new email is found, return None
    logger.info("No new email found")
    return None
