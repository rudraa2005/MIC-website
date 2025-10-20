import smtplib
from dotenv import dotenv_values
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import json
import base64
from pathlib import Path
from groq import Groq
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

base_dir = Path(__file__).resolve().parent
env_path = base_dir / '.env'
env_vars = dotenv_values(env_path)


class ProfessionalEmailSender:
    def __init__(self, groq_api_key=None, credentials_file=None, logo_path=None):
        """
        Initialize Professional Email Sender with OAuth2
        
        Args:
            groq_api_key: Your Groq API key (falls back to env GroqAPIKey)
            credentials_file: Path to Google OAuth2 credentials JSON file
            logo_path: Path to MIC logo file (defaults to 'mic_logo.png' in same directory)
        """
        resolved_groq_key = (
            groq_api_key
            or os.environ.get('GROQ_API_KEY')
            or os.environ.get('GroqAPIKey')
            or env_vars.get('GroqAPIKey')
        )

        print(f"🔍 DEBUG: Looking for Groq API key...")
        print(f"   - Passed as parameter: {bool(groq_api_key)}")
        print(f"   - Found in os.environ: {bool(os.environ.get('GROQ_API_KEY') or os.environ.get('GroqAPIKey'))}")
        print(f"   - Found in .env file: {bool(env_vars.get('GroqAPIKey'))}")
        print(f"   - .env file path: {env_path}")
        print(f"   - .env file exists: {env_path.exists()}")
        if resolved_groq_key:
            print(f"   ✓ API Key resolved: {resolved_groq_key[:20]}...")
        else:
            print(f"   ✗ No API key found - will use fallback emails")

        self.groq_client = Groq(api_key=resolved_groq_key) if resolved_groq_key else None

        base_dir = Path(__file__).resolve().parent
        default_credentials = base_dir / 'credentials.json'
        self.credentials_file = str(credentials_file or os.environ.get('GOOGLE_CREDENTIALS_JSON', default_credentials))

        default_logo = base_dir / 'static' / 'uploads' / 'mic_mail.jpg'
        self.logo_path = str(logo_path or os.environ.get('MIC_LOGO_PATH', default_logo))

        if os.path.exists(self.logo_path):
            print(f"✓ MIC logo found at: {self.logo_path}")
        else:
            print(f"⚠️  MIC logo not found at: {self.logo_path}")
            print(f"   Emails will be sent without logo attachment")

        self.gmail_service = None
        self._authenticate_gmail()

    def _authenticate_gmail(self):
        """Authenticate with Gmail using OAuth2 (Render-compatible)."""
        creds = None
        token_path = "token.json"
        credentials_path = "credentials.json"

        # ✅ Step 1: Write credentials from Render env vars (if available)
        if os.getenv("GOOGLE_CREDENTIALS"):
            with open(credentials_path, "w") as f:
                f.write(os.getenv("GOOGLE_CREDENTIALS"))
            print("✓ credentials.json written from Render environment variable")

        # ✅ Step 2: Write token.json from Render env vars (if available)
        if os.getenv("GOOGLE_TOKEN"):
            with open(token_path, "w") as f:
                f.write(os.getenv("GOOGLE_TOKEN"))
            print("✓ token.json written from Render environment variable")

        # ✅ Step 3: Load token if it exists
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # ✅ Step 4: Refresh or create credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                print("🔄 Token refreshed successfully")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                    print("💾 New token.json saved locally")

        # ✅ Step 5: Build Gmail service
        self.gmail_service = build("gmail", "v1", credentials=creds)
        print("✅ Successfully authenticated with Gmail")

    def generate_email_content(self, context, additional_instructions=""):
        """
        Generate professional email content using Groq AI
        """
        prompt = f"""Generate a professional email based on the following context:

Context: {context}

Additional Instructions: {additional_instructions}

Please provide:
1. A clear and professional subject line
2. A well-structured professional email body with proper greeting and closing

Format your response as:
SUBJECT: [subject line here]
BODY:
[email body here]
"""

        try:
            if not self.groq_client:
                print("⚠️  Using fallback email (Groq client not initialized)")
                return {
                    'subject': 'Welcome to MIC Innovation Newsletter',
                    'body': (
                        'Hello,\n\n'
                        'Thank you for subscribing to the MIC Innovation Centre newsletter. '
                        'You\'ll receive updates about events, resources, and opportunities.\n\n'
                        'Best regards,\nMIC Innovation Centre'
                    )
                }

            print("🤖 Generating email with Groq AI...")
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional email writing assistant. "
                            "Write SHORT, warm, and friendly emails that feel natural and conversational. "
                            "Keep it brief (3–5 sentences max). Avoid corporate jargon or overly formal language. "
                            "Be genuine and human. Always include a natural greeting and sign-off."
                            "Make it so that the email sent is spam proof i.e. the mail app doesnt sent the mail to the spam folder automatically hence use words to protect it from getting sent to spam folder automatically"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=500,
            )

            response = chat_completion.choices[0].message.content
            print("✓ Email content generated successfully")

            subject = ""
            body = ""
            lines = response.split("\n")
            capturing_body = False

            for line in lines:
                if line.startswith("SUBJECT:"):
                    subject = line.replace("SUBJECT:", "").strip()
                elif line.startswith("BODY:"):
                    capturing_body = True
                elif capturing_body:
                    body += line + "\n"

            return {"subject": subject, "body": body.strip()}

        except Exception as e:
            print(f"✗ Error generating email content: {str(e)}")
            print("   Falling back to default email")
            return {
                'subject': 'Welcome to MIC Innovation Newsletter',
                'body': (
                    'Hello,\n\n'
                    'Thank you for subscribing to the MIC Innovation Centre newsletter. '
                    'You\'ll receive updates about events, resources, and opportunities.\n\n'
                    'Best regards,\nMIC Innovation Centre'
                ),
            }

    def create_message(self, to, subject, body, attachment_path=None, include_logo=True):
        """Create email message with optional attachments"""
        message = MIMEMultipart()
        message["To"] = to
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        if include_logo and os.path.exists(self.logo_path):
            try:
                with open(self.logo_path, "rb") as logo_file:
                    logo_part = MIMEBase("application", "octet-stream")
                    logo_part.set_payload(logo_file.read())

                encoders.encode_base64(logo_part)
                logo_filename = os.path.basename(self.logo_path)
                logo_part.add_header("Content-Disposition", f"attachment; filename={logo_filename}")
                message.attach(logo_part)
                print(f"✓ MIC logo attached: {logo_filename}")
            except Exception as e:
                print(f"⚠️  Could not attach logo: {e}")

        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                filename = os.path.basename(attachment_path)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                message.attach(part)
                print(f"✓ Additional attachment added: {filename}")
            except Exception as e:
                print(f"⚠️  Could not attach file: {e}")

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw_message}

    def send_email(self, recipient_email, subject, body, attachment_path=None, include_logo=True):
        """Send email with optional attachments"""
        try:
            message = self.create_message(recipient_email, subject, body, attachment_path, include_logo)
            sent_message = self.gmail_service.users().messages().send(userId="me", body=message).execute()

            print(f"✓ Email sent successfully to {recipient_email}")
            print(f"  Message ID: {sent_message['id']}")
            return True
        except HttpError as error:
            print(f"✗ Failed to send email: {error}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error sending email: {e}")
            return False

    def compose_and_send(self, recipient_email, context, additional_instructions="", attachment_path=None, preview=False, include_logo=True):
        """Generate professional email content with AI and send it"""
        print("🤖 Generating email...")
        email_content = self.generate_email_content(context, additional_instructions)

        if not email_content:
            print("Failed to generate email content")
            return False

        if preview:
            print("\n" + "=" * 60)
            print("📧 GENERATED EMAIL PREVIEW")
            print("=" * 60)
            print(f"To: {recipient_email}")
            print(f"Subject: {email_content['subject']}")
            print("-" * 60)
            print(email_content['body'])
            if include_logo and os.path.exists(self.logo_path):
                print(f"\n📎 Attachments: {os.path.basename(self.logo_path)}")
            if attachment_path:
                print(f"📎 Additional: {os.path.basename(attachment_path)}")
            print("=" * 60 + "\n")

        return self.send_email(recipient_email, email_content['subject'], email_content['body'], attachment_path, include_logo)

    def send_welcome_email(self, recipient_email):
        """Send welcome email with MIC logo attached"""
        context = (
            "Send a warm welcome email to a new subscriber of the MAHE Innovation Centre "
            "newsletter. Thank them for subscribing, set expectations about receiving event "
            "announcements and resources, and include a friendly sign-off."
        )
        return self.compose_and_send(recipient_email, context)

    def send_event_announcement(self, recipient_email, event_title, event_date=None, location=None, description=None):
        """Send event announcement email with MIC logo attached"""
        details = []
        if event_date:
            details.append(f"Date: {event_date}")
        if location:
            details.append(f"Location: {location}")
        details_text = "\n".join(details)
        context = (
            f"Announce a new event to newsletter subscribers.\n"
            f"Title: {event_title}\n"
            f"{details_text}\n"
            f"Description: {description or ''}\n"
            "Encourage registration/participation and keep tone professional and concise."
        )
        return self.compose_and_send(recipient_email, context)


if __name__ == "__main__":
    GROQ_API_KEY = env_vars.get("GroqAPIKey")
    email_sender = ProfessionalEmailSender(GROQ_API_KEY)
