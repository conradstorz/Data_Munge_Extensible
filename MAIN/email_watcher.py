import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import os
from threading import Timer
from loguru import logger
import re


class EmailAttachmentDownloader:
    def __init__(self, email_user, email_password, download_folder, interval=600, uid_file='downloaded_uids.pkl'):
        self.email_user = email_user
        self.email_password = email_password
        self.download_folder = download_folder
        self.interval = interval  # Time interval in seconds
        self.timer = None
        self.uid_file = uid_file
        self.downloaded_uids = self.load_uid_status()

    def load_uid_status(self):
        try:
            with open(self.uid_file, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return set()

    def save_uid_status(self):
        with open(self.uid_file, 'wb') as f:
            pickle.dump(self.downloaded_uids, f)

    def download_attachments(self):
        ignored_extensions = [
            ".exe",
            ".bat",
            ".tmp",
            ".gif",
            "html",
            ".pdf",
            ".jpg",
        ]  # Specify the extensions to ignore
        try:
            with imaplib.IMAP4_SSL('imap.gmail.com') as mail:
                mail.login(self.email_user, self.email_password)
                mail.select('inbox')

                # Calculate the date 24 hours ago
                date_since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")

                # Search for emails since the calculated date
                result, data = mail.search(None, f'(SINCE "{date_since}")')
                if result != "OK":
                    logger.error("No messages found!")
                    return

                for uid in data[0].split():
                    if uid in self.downloaded_uids:
                        print(f'Already downloaded: UID {uid}')
                        continue

                    result, email_data = mail.uid('fetch', uid, '(RFC822)')
                    if result != 'OK':
                        print(f'Failed to fetch email UID {uid}')
                        continue

                    msg = email.message_from_bytes(email_data[0][1])
                    print(f'Processing email UID {uid}')

                    # Iterate over email parts
                    for part in msg.walk():
                        if (
                            part.get_content_maintype() == 'multipart'
                            or part.get('Content-Disposition') is None
                        ):
                            continue

                        filename = part.get_filename()
                        if filename:
                            decoded_header = decode_header(filename)
                            filename, encoding = decoded_header[0]
                            if isinstance(filename, bytes):
                                filename = filename.decode(encoding or 'utf-8')

                            # Check file extension and skip if it's in the ignored list
                            file_extension = os.path.splitext(filename)[1].lower()
                            if file_extension in ignored_extensions:
                                logger.debug(f"Ignored: {filename}")
                                continue

                            # Sanitize filename
                            safe_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
                            filepath = os.path.join(self.download_folder, safe_filename)

                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            print(f'Downloaded: {safe_filename}')

                            self.downloaded_uids.add(uid)
                            self.save_uid_status()

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


class EmailTextDownloader:
    def __init__(
        self,
        email_user,
        email_password,
        download_folder,
        interval=600,
        sender_email=None,
    ):
        self.email_user = email_user
        self.email_password = email_password
        self.download_folder = download_folder
        self.interval = interval  # Time interval in seconds
        self.sender_email = sender_email
        self.timer = None

    def download_text_from_sender(self):
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com") as mail:
                mail.login(self.email_user, self.email_password)
                mail.select("inbox")

                # Calculate the date 24 hours ago
                date_24_hours_ago = (datetime.now() - timedelta(days=1)).strftime(
                    "%d-%b-%Y"
                )

                # Construct search criteria to include only emails from the last 24 hours and from the specific sender
                search_criteria = f"(SINCE {date_24_hours_ago})"
                if self.sender_email:
                    search_criteria = (
                        f'(FROM "{self.sender_email}" SINCE {date_24_hours_ago})'
                    )

                result, data = mail.search(None, search_criteria)
                if result != "OK":
                    logger.error("No messages found!")
                    return

                for num in data[0].split():
                    result, data = mail.fetch(num, "(RFC822)")
                    if result != "OK":
                        logger.error(f"Failed to fetch email {num}")
                        continue

                    msg = email.message_from_bytes(data[0][1])
                    logger.info(f"Processing email {num} from {self.sender_email}")

                    # Get the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    # Decode email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if (
                                part.get_content_type() == "text/plain"
                                and part.get("Content-Disposition") is None
                            ):
                                body = part.get_payload(decode=True).decode("utf-8")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8")

                    # Save the email text to a file
                    safe_subject = "".join(c if c.isalnum() else "_" for c in subject)
                    filepath = os.path.join(self.download_folder, f"{safe_subject}.txt")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(body)

                    logger.info(f"Downloaded email text: {filepath}")

                mail.logout()
        except Exception as e:
            logger.error(f"Error downloading email text: {e}")

    def check_for_emails(self):
        logger.info("Checking for new emails from the specified sender...")
        self.download_text_from_sender()
        self.timer = Timer(self.interval, self.check_for_emails)
        self.timer.start()

    def start(self):
        self.check_for_emails()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()


"""example usage

downloader = EmailTextDownloader(
    email_user="your_email@gmail.com",
    email_password="your_app_specific_password",
    download_folder="/path/to/your/download/folder",
    interval=300,  # check every 5 minutes
    sender_email="specific.sender@example.com"  # the sender you want to monitor
)
downloader.start()

"""
