import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def sendTestEmail(email, subject, body):
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USER = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM')

    print(f"SMTP_HOST: {SMTP_HOST}")
    print(f"SMTP_PORT: {SMTP_PORT}")
    print(f"SMTP_USER: {SMTP_USER}")
    print(f"SMTP_PASSWORD: {SMTP_PASSWORD}")
    print(f"SMTP_FROM: {SMTP_FROM}")

    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM]):
        print("Error: Missing environment variables for email configuration.")
        return False

    msg = MIMEMultipart()
    msg['From'] = SMTP_FROM
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT))
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, email, msg.as_string())
        server.quit()
        print("Test email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send test email: {e}")
        return False

def main():
    # Define the test email details
    test_email = os.getenv('MAIL_TO')
    test_subject = "Test Email from Wyze Lock Airbnb Script"
    test_body = "This is a test email to verify the email configuration."
    
    # Send test email
    sendTestEmail(test_email, test_subject, test_body)

if __name__ == "__main__":
    main()