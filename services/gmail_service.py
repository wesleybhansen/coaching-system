import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, parseaddr
import logging
import time
import random

import config

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds, doubles each retry


def _retry(func, *args, **kwargs):
    """Retry a Gmail operation with exponential backoff."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Gmail operation failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Gmail operation failed after {MAX_RETRIES} attempts: {e}")
    raise last_error

# Emails from these patterns are ignored (no-reply, system notifications, etc.)
IGNORED_SENDERS = [
    "noreply", "no-reply", "no_reply",
    "support@",
    "mailer-daemon", "postmaster",
    "notifications", "notify",
    "calendar-notification",
    "workspace-noreply",
    "admin@google", "admin@workspace",
    "googleworkspace",
    "accounts.google",
]


def _is_ignored_sender(from_addr: str) -> bool:
    """Return True if this sender should be ignored."""
    addr = from_addr.lower()
    return any(pattern in addr for pattern in IGNORED_SENDERS)


def _imap_connect():
    conn = imaplib.IMAP4_SSL(config.GMAIL_IMAP_HOST)
    conn.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
    return conn


def _smtp_connect():
    server = smtplib.SMTP(config.GMAIL_SMTP_HOST, config.GMAIL_SMTP_PORT)
    server.starttls()
    server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
    return server


def fetch_unread_emails(max_results: int = 50) -> list[dict]:
    """Fetch unread emails from inbox, excluding emails from our own address."""
    def _fetch():
        conn = _imap_connect()
        try:
            conn.select("INBOX")
            _, msg_nums = conn.search(None, "UNSEEN")
            if not msg_nums[0]:
                return []

            message_ids = msg_nums[0].split()[:max_results]
            emails = []

            for msg_id in message_ids:
                _, msg_data = conn.fetch(msg_id, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                from_addr = parseaddr(msg["From"])[1].lower()
                if from_addr == config.GMAIL_ADDRESS.lower():
                    continue
                if _is_ignored_sender(from_addr):
                    # Auto-mark system emails as read so they don't pile up
                    conn.store(msg_id, "+FLAGS", "\\Seen")
                    logger.info(f"Ignoring system email from {from_addr}")
                    continue

                body = _extract_body(msg)
                message_id_header = msg.get("Message-ID", "")
                in_reply_to = msg.get("In-Reply-To", "")
                references = msg.get("References", "")

                emails.append({
                    "imap_id": msg_id.decode(),
                    "message_id": message_id_header,
                    "from_email": from_addr,
                    "from_name": parseaddr(msg["From"])[0],
                    "subject": msg.get("Subject", ""),
                    "body": body,
                    "in_reply_to": in_reply_to,
                    "references": references,
                    "date": msg.get("Date", ""),
                })

            return emails
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    return _retry(_fetch)


def mark_as_read(imap_id: str):
    """Mark a specific email as read by IMAP sequence number."""
    def _mark():
        conn = _imap_connect()
        try:
            conn.select("INBOX")
            conn.store(imap_id.encode(), "+FLAGS", "\\Seen")
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    _retry(_mark)


def mark_multiple_as_read(imap_ids: list[str]):
    """Mark multiple emails as read in a single connection."""
    if not imap_ids:
        return

    def _mark_batch():
        conn = _imap_connect()
        try:
            conn.select("INBOX")
            for imap_id in imap_ids:
                conn.store(imap_id.encode(), "+FLAGS", "\\Seen")
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    _retry(_mark_batch)


def send_email(to_email: str, subject: str, body: str, in_reply_to: str = None,
               references: str = None, delay_seconds: int = 0):
    """Send an email, optionally as a reply in a thread."""
    if not to_email or not to_email.strip():
        logger.error("send_email called with empty to_email, skipping")
        return None

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("Wes", config.GMAIL_ADDRESS))
    msg["To"] = to_email
    msg["Subject"] = subject

    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = references or in_reply_to

    # Plain text body
    msg.attach(MIMEText(body, "plain"))

    def _send():
        server = _smtp_connect()
        try:
            server.sendmail(config.GMAIL_ADDRESS, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}: {subject}")
        finally:
            try:
                server.quit()
            except Exception:
                pass

    _retry(_send)
    return msg["Message-ID"]


def send_coaching_response(to_email: str, body: str, in_reply_to: str = None,
                           references: str = None):
    """Send a coaching response as a reply in the existing thread."""
    # Add sign-off
    full_body = f"{body}\n\nWes"

    # Random delay 0-30 minutes to feel human
    delay = random.randint(0, 30 * 60)

    return send_email(
        to_email=to_email,
        subject="Re: Coaching",
        body=full_body,
        in_reply_to=in_reply_to,
        references=references,
        delay_seconds=delay,
    )


def send_checkin(to_email: str, first_name: str, in_reply_to: str = None,
                 references: str = None):
    """Send a check-in email."""
    body = f"""Hey {first_name},

Just wanted to quickly check-in and see how things are going. Please reply with:

1. Accomplished - What did you get done since we last talked?
2. Current Focus - What are you working on now?
3. Next Step - What's the single most important thing you need to do next?
4. Approach - How are you going about it?

There's no need to spend a ton of time on this. A sentence or two for each is plenty.

Wes"""

    return send_email(
        to_email=to_email,
        subject="Coaching Check-In",
        body=body,
    )


def get_onboarding_body(first_name: str) -> str:
    """Return the onboarding email body text without sending."""
    return f"""Hey {first_name},

Welcome to coaching. Here's how this works:

A couple times a week, I'll check in with a few quick questions about what you're working on. You reply (should take about 5 minutes), and I'll send back focused feedback - usually within a day or so.

That's it. Short exchanges, consistent momentum.

Before we start, I need some context from you. Reply to this email with:

1. Where you're at right now:
   - Still figuring out the idea (Ideation)
   - Testing if people want this (Early Validation)
   - Have some traction, refining the model (Late Validation)
   - Growing and scaling (Growth)
2. Your biggest challenge or question right now
3. If you have one, your current business idea (2-3 sentences is fine; if you don't yet have an idea, this is where we'll get started)

Once I hear back, we'll get started.

Talk soon,
Wes"""


def send_onboarding(to_email: str, first_name: str):
    """Send the onboarding email to a new user."""
    body = f"""Hey {first_name},

Welcome to coaching. Here's how this works:

A couple times a week, I'll check in with a few quick questions about what you're working on. You reply (should take about 5 minutes), and I'll send back focused feedback - usually within a day or so.

That's it. Short exchanges, consistent momentum.

Before we start, I need some context from you. Reply to this email with:

1. Where you're at right now:
   - Still figuring out the idea (Ideation)
   - Testing if people want this (Early Validation)
   - Have some traction, refining the model (Late Validation)
   - Growing and scaling (Growth)
2. Your biggest challenge or question right now
3. If you have one, your current business idea (2-3 sentences is fine; if you don't yet have an idea, this is where we'll get started)

Once I hear back, we'll get started.

Talk soon,
Wes"""

    return send_email(
        to_email=to_email,
        subject="Let's get you moving forward",
        body=body,
    )


def send_reengagement(to_email: str, first_name: str, in_reply_to: str = None,
                      references: str = None):
    """Send a re-engagement nudge."""
    body = f"""Hey {first_name},

Haven't heard from you in a bit. Everything okay?

When you're ready, just reply with a quick update on what you're working on.

Wes"""

    return send_email(
        to_email=to_email,
        subject="Re: Coaching",
        body=body,
        in_reply_to=in_reply_to,
        references=references,
    )


def send_pause_confirmation(to_email: str, in_reply_to: str = None,
                            references: str = None):
    body = "No problem - I'll pause check-ins for now. Just reply 'resume' whenever you're ready to pick back up.\n\nWes"
    return send_email(to_email, "Re: Coaching", body, in_reply_to, references)


def send_resume_confirmation(to_email: str, in_reply_to: str = None,
                             references: str = None):
    body = "Welcome back! I'll resume the regular check-ins. You'll hear from me soon.\n\nWes"
    return send_email(to_email, "Re: Coaching", body, in_reply_to, references)


def fetch_old_unread_emails(max_results: int = 100) -> list[dict]:
    """Fetch unread emails older than 24 hours (for cleanup workflow)."""
    def _fetch():
        conn = _imap_connect()
        try:
            conn.select("INBOX")
            # Search for unseen emails older than 1 day
            _, msg_nums = conn.search(None, "(UNSEEN BEFORE " +
                                      time.strftime("%d-%b-%Y", time.gmtime(time.time() - 86400)) + ")")
            if not msg_nums[0]:
                return []

            message_ids = msg_nums[0].split()[:max_results]
            emails = []

            for msg_id in message_ids:
                _, msg_data = conn.fetch(msg_id, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                from_addr = parseaddr(msg["From"])[1].lower()
                if from_addr == config.GMAIL_ADDRESS.lower() or _is_ignored_sender(from_addr):
                    conn.store(msg_id, "+FLAGS", "\\Seen")
                    continue

                body = _extract_body(msg)

                emails.append({
                    "imap_id": msg_id.decode(),
                    "message_id": msg.get("Message-ID", ""),
                    "from_email": from_addr,
                    "from_name": parseaddr(msg["From"])[0],
                    "subject": msg.get("Subject", ""),
                    "body": body,
                    "in_reply_to": msg.get("In-Reply-To", ""),
                    "references": msg.get("References", ""),
                    "date": msg.get("Date", ""),
                })

            return emails
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    return _retry(_fetch)


def _extract_body(msg) -> str:
    """Extract plain text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    return part.get_payload(decode=True).decode("latin-1", errors="replace")
        # Fallback: try HTML
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    return ""
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception:
            return msg.get_payload(decode=True).decode("latin-1", errors="replace")
    return ""
