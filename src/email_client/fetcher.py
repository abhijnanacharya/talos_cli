from datetime import datetime, timedelta
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

def fetch_recent_emails():
    imap = imaplib.IMAP4_SSL(IMAP_SERVER)
    imap.login(EMAIL, EMAIL_APP_PASSWORD)
    imap.select("inbox")

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
    status, messages = imap.search(None, f'SINCE {yesterday}')
    email_ids = messages[0].split()

    emails = []

    for eid in email_ids:
        res, msg_data = imap.fetch(eid, "(RFC822)")
        for response in msg_data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])

                # Decode subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition") or "")

                        if "attachment" in content_disposition:
                            continue

                        charset = part.get_content_charset() or "utf-8"
                        try:
                            payload = part.get_payload(decode=True).decode(charset, errors="ignore")
                        except Exception:
                            continue

                        if content_type == "text/plain":
                            body = payload.strip()
                            break  # Prefer plain text
                        elif content_type == "text/html" and not body:
                            soup = BeautifulSoup(payload, "html.parser")
                            body = soup.get_text(separator="\n", strip=True)
                else:
                    content_type = msg.get_content_type()
                    charset = msg.get_content_charset() or "utf-8"
                    payload = msg.get_payload(decode=True).decode(charset, errors="ignore")

                    if content_type == "text/plain":
                        body = payload.strip()
                    elif content_type == "text/html":
                        soup = BeautifulSoup(payload, "html.parser")
                        body = soup.get_text(separator="\n", strip=True)

                emails.append((subject, body))

    imap.logout()
    return emails
