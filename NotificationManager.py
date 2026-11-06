import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def sendEmail(codeText):
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    raw_recipients = os.getenv("RECIPIENTS_LIST")
    recipients = [r.strip() for r in raw_recipients.split(",")]

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
 
            for recipient in recipients:
                msg = MIMEMultipart()
                msg["From"] = SENDER_EMAIL
                msg["To"] = recipient
                msg["Subject"] = "Cash Cow Code (from: Zenit)"            

                msg.attach(MIMEText(codeText, "plain"))
                
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                print(f"Success! Message sent to {recipient}")
                
    except Exception as e:
        print(f"An error occurred: {e}")