"""Export corrected coaching responses in OpenAI fine-tuning format.

Usage:
    python scripts/export_finetune_data.py [output_file]

The output file defaults to 'finetune_data.jsonl' in the project root.
Each line is a JSON object with the format:
{
    "messages": [
        {"role": "system", "content": "You are Wes, an entrepreneurship coach..."},
        {"role": "user", "content": "user's message + context"},
        {"role": "assistant", "content": "corrected response"}
    ]
}
"""

import json
import sys
import os
import argparse

# Add project root to path so we can import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import supabase_client as db
from services import openai_service


def load_system_message() -> str:
    """Load the assistant instructions from prompts/assistant_instructions.md."""
    instructions_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "assistant_instructions.md"
    )
    with open(instructions_path) as f:
        return f.read().strip()


def build_user_message(correction: dict, user: dict | None) -> str:
    """Build the user message combining context and the original message.

    Includes the user's stage, business idea, and summary when available,
    followed by the original user message that triggered the correction.
    """
    parts = []

    # Add user context if we have a user record
    if user:
        stage = user.get("stage", "Unknown")
        parts.append(f"Stage: {stage}")

        business_idea = user.get("business_idea")
        if business_idea:
            parts.append(f"Business Idea: {business_idea}")

        summary = user.get("summary")
        if summary:
            parts.append(f"Summary: {summary}")

    # Add the original user message
    original_message = correction.get("original_message") or ""
    if original_message:
        if parts:
            parts.append("")  # blank line separator
        parts.append(f"User Message: {original_message}")
    elif not parts:
        # No context and no message -- this entry won't be useful
        return ""

    return "\n".join(parts)


def export_finetune_data(output_path: str, min_corrections: int = 0) -> dict:
    """Fetch corrections from Supabase and write JSONL fine-tuning file.

    Args:
        output_path: Path to the output .jsonl file.
        min_corrections: Minimum number of corrections required to proceed.

    Returns:
        Dict with keys: total, exported, skipped.
    """
    # Load system prompt
    try:
        system_message = load_system_message()
    except FileNotFoundError:
        print("Error: Could not find prompts/assistant_instructions.md")
        sys.exit(1)

    # Fetch all corrections from the database
    try:
        corrections = db.get_all_corrections()
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    total = len(corrections)
    print(f"Found {total} correction(s) in database.")

    # Check minimum threshold
    if total < min_corrections:
        print(
            f"Only {total} correction(s) found, but --min-corrections requires "
            f"at least {min_corrections}. Skipping export."
        )
        return {"total": total, "exported": 0, "skipped": total}

    exported = 0
    skipped = 0

    with open(output_path, "w") as f:
        for correction in corrections:
            # Skip entries without a corrected response
            corrected_response = (correction.get("corrected_response") or "").strip()
            if not corrected_response:
                skipped += 1
                continue

            # Try to get user context from the linked conversation
            user = None
            conversation_data = correction.get("conversations")
            if conversation_data:
                user_id = conversation_data.get("user_id")
                if user_id:
                    try:
                        user = db.get_user_by_id(user_id)
                    except Exception as e:
                        print(f"  Warning: Could not fetch user {user_id}: {e}")

            # Build the user message with context
            user_message = build_user_message(correction, user)
            if not user_message:
                # No usable content for the user turn
                skipped += 1
                continue

            # Construct the fine-tuning example
            example = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": corrected_response},
                ]
            }

            f.write(json.dumps(example) + "\n")
            exported += 1

    return {"total": total, "exported": exported, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(
        description="Export corrected coaching responses in OpenAI fine-tuning JSONL format."
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="finetune_data.jsonl",
        help="Output JSONL file path (default: finetune_data.jsonl)",
    )
    parser.add_argument(
        "--min-corrections",
        type=int,
        default=0,
        help="Minimum number of corrections required to export (default: 0)",
    )
    args = parser.parse_args()

    output_path = args.output_file

    print(f"Exporting fine-tuning data to: {output_path}")
    print()

    stats = export_finetune_data(output_path, min_corrections=args.min_corrections)

    print()
    print("--- Export Summary ---")
    print(f"  Total corrections:  {stats['total']}")
    print(f"  Exported:           {stats['exported']}")
    print(f"  Skipped:            {stats['skipped']}")

    if stats["exported"] > 0:
        print(f"\nFile written: {output_path}")
        print("Upload to OpenAI with:")
        print(f"  openai api fine_tunes.create -t {output_path} -m gpt-4o-mini-2024-07-18")
    elif stats["total"] > 0:
        print("\nNo examples were exported. Check that corrections have a corrected_response.")
    else:
        print("\nNo corrections found in the database yet.")


if __name__ == "__main__":
    main()
