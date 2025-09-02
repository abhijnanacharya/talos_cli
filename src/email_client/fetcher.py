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

def _sanitize_charset(cs: str | None) -> str:
    if not cs:
        return "utf-8"
    cs = cs.lower()
    if cs in ("unknown-8bit", "x-unknown", "binary"):
        return "utf-8"
    return cs

def _safe_decode_header(value: str | None) -> str:
    if not value:
        return ""
    out = []
    for part, cs in decode_header(value):
        if isinstance(part, bytes):
            cs = _sanitize_charset(cs)
            try:
                out.append(part.decode(cs, errors="replace"))
            except LookupError:
                out.append(part.decode("utf-8", errors="replace"))
        else:
            out.append(part)
    return "".join(out)

def _safe_decode_bytes(raw: bytes | None, cs: str | None) -> str:
    if not raw:
        return ""
    cs = _sanitize_charset(cs)
    try:
        return raw.decode(cs, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def fetch_recent_emails():
    imap = imaplib.IMAP4_SSL(IMAP_SERVER)
    imap.login(EMAIL, EMAIL_APP_PASSWORD)
    imap.select("inbox")

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
    status, messages = imap.search(None, f'SINCE {yesterday}')
    email_ids = messages[0].split() if status == "OK" and messages and messages[0] else []

    emails = []

    for eid in email_ids:
        res, msg_data = imap.fetch(eid, "(RFC822)")
        if res != "OK":
            continue

        for response in msg_data:
            if not isinstance(response, tuple):
                continue

            msg = email.message_from_bytes(response[1])

            # Safe subject decode
            subject = _safe_decode_header(msg["Subject"])

            body = ""
            if msg.is_multipart():
                # Prefer text/plain; fall back to text/html
                html_fallback = ""
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition") or "")
                    if "attachment" in content_disposition:
                        continue

                    charset = _sanitize_charset(part.get_content_charset())
                    payload_bytes = part.get_payload(decode=True)
                    if payload_bytes is None:
                        continue

                    payload = _safe_decode_bytes(payload_bytes, charset)

                    if content_type == "text/plain" and payload.strip():
                        body = payload.strip()
                        break  # got preferred content
                    elif content_type == "text/html" and not html_fallback:
                        soup = BeautifulSoup(payload, "html.parser")
                        html_fallback = soup.get_text(separator="\n", strip=True)

                if not body and html_fallback:
                    body = html_fallback
            else:
                content_type = msg.get_content_type()
                charset = _sanitize_charset(msg.get_content_charset())
                payload_bytes = msg.get_payload(decode=True)
                payload = _safe_decode_bytes(payload_bytes, charset) if payload_bytes else ""

                if content_type == "text/plain":
                    body = (payload or "").strip()
                elif content_type == "text/html":
                    soup = BeautifulSoup(payload, "html.parser")
                    body = soup.get_text(separator="\n", strip=True)

            emails.append((subject, body))

    imap.logout()
    return emails