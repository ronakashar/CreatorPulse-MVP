import os
import requests


def send_email(*, to_email: str, subject: str, html_content: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY not set")

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Prefer configured FROM; fallback to Resend onboarding sender for dev/testing
    from_email = os.getenv("RESEND_FROM", "Acme <onboarding@resend.dev>")
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    if resp.status_code >= 400:
        msg_hint = ""
        if resp.status_code == 403 and "domain is not verified" in resp.text.lower():
            msg_hint = " Hint: set RESEND_FROM to 'onboarding@resend.dev' for local tests or verify your domain in Resend."
        raise RuntimeError(f"Resend error: {resp.status_code} {resp.text}{msg_hint}")


