import os
import resend

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_link = f"{BASE_URL}/reset-password.html?token={token}"

    if not RESEND_API_KEY:
        # No API key configured yet — log the link instead of failing,
        # so local dev works without setting up email at all
        print(f"[DEV MODE — no email configured] Reset link for {to_email}: {reset_link}")
        return

    resend.Emails.send({
        "from": EMAIL_FROM,
        "to": [to_email],
        "subject": "Reset your Sitendra Notes password",
        "html": (
            f"<p>We received a request to reset your password.</p>"
            f"<p><a href=\"{reset_link}\">Click here to choose a new password</a>. "
            f"This link expires in 30 minutes.</p>"
            f"<p>If you didn't request this, you can safely ignore this email.</p>"
        ),
    })
# export RESEND_API_KEY="re_ThmBpiMx_6VYw8hFUwoK7oei65RugJSof"
# export BASE_URL="http://127.0.0.1:8000"