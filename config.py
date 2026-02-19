import os
import sys
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


def _require(var_name: str) -> str:
    """Get a required environment variable or exit with a clear error message."""
    value = os.environ.get(var_name)
    if not value or not value.strip():
        print(f"ERROR: Required environment variable '{var_name}' is missing or empty.", file=sys.stderr)
        print(f"Set it in your .env file or in GitHub Actions secrets.", file=sys.stderr)
        sys.exit(1)
    return value.strip()


# Supabase
SUPABASE_URL = _require("SUPABASE_URL")
SUPABASE_KEY = _require("SUPABASE_KEY")

# OpenAI
OPENAI_API_KEY = _require("OPENAI_API_KEY")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "vs_6985fa853f84819196e012018b0defca")

# Gmail
GMAIL_ADDRESS = _require("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = _require("GMAIL_APP_PASSWORD")
GMAIL_IMAP_HOST = os.environ.get("GMAIL_IMAP_HOST", "imap.gmail.com")
GMAIL_SMTP_HOST = os.environ.get("GMAIL_SMTP_HOST", "smtp.gmail.com")
try:
    GMAIL_SMTP_PORT = int(os.environ.get("GMAIL_SMTP_PORT", "587"))
except ValueError:
    print(f"ERROR: GMAIL_SMTP_PORT must be a number, got '{os.environ.get('GMAIL_SMTP_PORT')}'", file=sys.stderr)
    sys.exit(1)

# Anthropic (optional — only needed when Anthropic is selected as AI provider)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Timezone
COACH_TIMEZONE = os.environ.get("COACH_TIMEZONE", "America/New_York")
