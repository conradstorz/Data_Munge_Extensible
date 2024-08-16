import imaplib
import email
from email.header import decode_header
import os
from threading import Timer
from loguru import logger
import re

class EmailAttachmentDownloader:
    def __init__(self, email_user, email_password, download_folder, interval=300):
        self.email_user = email_user
        self.email_password = email_password
        self.download_folder = download_folder
        self.interval = interval  # Time interval in seconds
        self.timer = None

    def download_attachments(self):
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com") as mail:
                mail.login(self.email_user, self.email_password)
                mail.select("inbox")

                # Calculate the date 24 hours ago
                date_since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")

                # Search for emails since the calculated date
                result, data = mail.search(None, f'(SINCE "{date_since}")')
                if result != "OK":
                    logger.error("No messages found!")
                    return

                for num in data[0].split():
                    result, email_data = mail.fetch(num, '(RFC822)')
                    if result != "OK":
                        logger.error(f"Failed to fetch email {num}")
                        continue

                    msg = email.message_from_bytes(email_data[0][1])
                    logger.info(f"Processing email {num}")

                    # Iterate over email parts
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                            continue

                        filename = part.get_filename()
                        if filename:
                            decoded_header = decode_header(filename)
                            filename, encoding = decoded_header[0]
                            if isinstance(filename, bytes):
                                filename = filename.decode(encoding or 'utf-8')

                            # Sanitize filename
                            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
                            filepath = os.path.join(self.download_folder, safe_filename)

                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            logger.info(f"Downloaded: {safe_filename}")

                mail.logout()
        except Exception as e:
            logger.error(f"Error downloading attachments: {e}")


    def check_for_attachments(self):
        logger.info("Checking for new email attachments...")
        self.download_attachments()
        self.timer = Timer(self.interval, self.check_for_attachments)
        self.timer.start()

    def start(self):
        self.check_for_attachments()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
