import os
from dotenv import load_dotenv

load_dotenv()

# Streamlit Community Cloud stores secrets in st.secrets, not os.environ.
# Copy them into os.environ so the rest of the code works unchanged.
try:
    import streamlit as st
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ.setdefault(key, value)
except Exception:
    pass

# Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "vs_6985fa853f84819196e012018b0defca")

# Gmail
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
GMAIL_IMAP_HOST = os.environ.get("GMAIL_IMAP_HOST", "imap.gmail.com")
GMAIL_SMTP_HOST = os.environ.get("GMAIL_SMTP_HOST", "smtp.gmail.com")
GMAIL_SMTP_PORT = int(os.environ.get("GMAIL_SMTP_PORT", "587"))

# Timezone
COACH_TIMEZONE = os.environ.get("COACH_TIMEZONE", "America/New_York")
