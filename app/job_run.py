import os
import argparse

from services.supabase_client import get_user_by_email, get_latest_draft, mark_latest_draft_sent
from services.content_fetcher import fetch_all_sources
from services.newsletter_generator import generate_and_save_draft
from services.resend_client import send_email
from utils.formatting import markdown_to_html


def run_for_email(email: str, *, temperature: float = 0.7, num_links: int = 5) -> None:
    user = get_user_by_email(email=email)
    if not user:
        raise SystemExit(f"User not found: {email}")
    user_id = user["id"]

    # 1) Fetch
    fetch_all_sources(user_id=user_id)

    # 2) Generate
    draft_text = generate_and_save_draft(user_id=user_id, selected_item_ids=None, temperature=temperature, num_links=num_links)
    if not draft_text:
        print("No draft generated (no content).")
        return

    # 3) Send
    html = markdown_to_html(draft_text)
    send_email(to_email=email, subject="Your CreatorPulse Draft", html_content=html)
    mark_latest_draft_sent(user_id=user_id)
    print("Draft sent.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run fetch→generate→send for a given user email")
    parser.add_argument("email", help="User email to run the job for")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--num-links", type=int, default=5)
    args = parser.parse_args()
    run_for_email(args.email, temperature=args.temperature, num_links=args.num_links)



