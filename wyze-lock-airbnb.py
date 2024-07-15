import os
import re
import time
import requests
import smtplib
import argparse
import schedule
from icalendar import Calendar
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dotenv import load_dotenv
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError, WyzeRequestError
from wyze_sdk.models.devices.locks import LockKeyPermission, LockKeyPeriodicity
from wyze_sdk.signature import CBCEncryptor, MD5Hasher

# Load environment variables from .env file
load_dotenv()

# Constants
HOMES = [
    {
        'name': os.getenv('HOME_1_NAME'),
        'ical_url': os.getenv('HOME_1_ICAL_URL'),
        'lock_device_mac': os.getenv('HOME_1_LOCK_DEVICE_MAC'),
        'check_in_time': os.getenv('HOME_1_CHECK_IN_TIME'),
        'check_out_time': os.getenv('HOME_1_CHECK_OUT_TIME')
    },
    {
        'name': os.getenv('HOME_2_NAME'),
        'ical_url': os.getenv('HOME_2_ICAL_URL'),
        'lock_device_mac': os.getenv('HOME_2_LOCK_DEVICE_MAC'),
        'check_in_time': os.getenv('HOME_2_CHECK_IN_TIME'),
        'check_out_time': os.getenv('HOME_2_CHECK_OUT_TIME')
    }
]
WYZE_ACCESS_TOKEN = os.getenv('WYZE_ACCESS_TOKEN')
WYZE_REFRESH_TOKEN = os.getenv('WYZE_REFRESH_TOKEN')

def sendEmail(home, lock, check_in, check_out):
    MAIL_TO = os.getenv('MAIL_TO')
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USER = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM')

    # Check if necessary environment variables are set
    if not all([MAIL_TO, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM]):
        print("Error: Missing environment variables for email configuration.")
        return False

    # Format the check-in and check-out times
    check_in_str = check_in.strftime('%d %B %Y %H:%M')
    check_out_str = check_out.strftime('%d %B %Y %H:%M')

    Email_Subject = f"Wyze Lock Update: {home}"
    Email_Body = f"""
    Wyze Lock Update for Home: {home}

    Lock Information:
    -----------------
    Lock: {lock}
    Duration: {check_in_str} - {check_out_str}

    This is an automated message.
    """

    msg = MIMEMultipart()
    msg['From'] = SMTP_FROM
    msg['To'] = MAIL_TO
    msg['Subject'] = Email_Subject
    msg.attach(MIMEText(Email_Body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT))
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, MAIL_TO, msg.as_string())
        server.quit()
        print("Email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# Function to refresh the access token
def refresh_access_token(refresh_token):
    url = "https://api.wyzecam.com/app/user/refresh_token"
    payload = {
        "app_ver": "wyze_developer_api",
        "app_version": "wyze_developer_api",
        "phone_id": "wyze_developer_api",
        "refresh_token": refresh_token,
        "sc": "wyze_developer_api",
        "sv": "wyze_developer_api",
        "ts": int(time.time() * 1000)
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        new_access_token = data['data']['access_token']
        new_refresh_token = data['data']['refresh_token']
        return new_access_token, new_refresh_token
    else:
        raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

# Function to get the client
def get_client():
    global WYZE_ACCESS_TOKEN, WYZE_REFRESH_TOKEN
    try:
        client = Client(token=WYZE_ACCESS_TOKEN)
        # Test if the access token is valid
        client.devices_list()
    except WyzeApiError as e:
        if "AccessTokenError" in str(e) or "access token expired" in str(e):
            print("Access token expired, refreshing...")
            try:
                WYZE_ACCESS_TOKEN, WYZE_REFRESH_TOKEN = refresh_access_token(WYZE_REFRESH_TOKEN)
                os.environ['WYZE_ACCESS_TOKEN'] = WYZE_ACCESS_TOKEN
                os.environ['WYZE_REFRESH_TOKEN'] = WYZE_REFRESH_TOKEN
                client = Client(token=WYZE_ACCESS_TOKEN)
            except Exception as refresh_error:
                print(f"Failed to refresh access token: {refresh_error}")
                raise e  # Re-raise the original error if refreshing fails
        else:
            raise e  # Re-raise the original error if it's not an access token issue
    return client

def fetch_airbnb_bookings(ical_url):
    response = requests.get(ical_url)
    response.raise_for_status()
    calendar = Calendar.from_ical(response.text)
    
    bookings = []
    for component in calendar.walk():
        if component.name == "VEVENT" and 'Reserved' in component.get('SUMMARY'):
            description = component.get('DESCRIPTION')
            phone_match = re.search(r'Phone Number \(Last 4 Digits\): (\d{4})', description)
            if phone_match:
                phone_last4 = phone_match.group(1)
                check_in = component.get('DTSTART').dt
                check_out = component.get('DTEND').dt
                days_stay = (check_out - check_in).days
                guest_name = f"{check_in.strftime('%a')}-{days_stay}days"
                bookings.append({
                    'check_in': check_in,
                    'check_out': check_out,
                    'guest_phone_last4': phone_last4,
                    'guest_name': guest_name
                })
    return bookings

def sendTestEmail(email, subject, body):
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USER = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM')

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

def list_upcoming_bookings(client, days=7):
    upcoming_bookings = []
    current_time = datetime.now()
    end_time = current_time + timedelta(days=days)

    for home in HOMES:
        bookings = fetch_airbnb_bookings(home['ical_url'])
        for booking in bookings:
            check_in = datetime.combine(booking['check_in'], datetime.min.time())
            check_out = datetime.combine(booking['check_out'], datetime.min.time())
            check_in = check_in.replace(hour=int(home['check_in_time'].split(':')[0]), minute=int(home['check_in_time'].split(':')[1]))
            check_out = check_out.replace(hour=int(home['check_out_time'].split(':')[0]), minute=int(home['check_out_time'].split(':')[1]))
            if current_time <= check_in <= end_time:
                upcoming_bookings.append({
                    'home': home['name'],
                    'check_in': check_in,
                    'check_out': check_out,
                    'access_code': booking['guest_phone_last4'],
                    'guest_name': booking['guest_name']
                })

    for booking in upcoming_bookings:
        print(f"Home: {booking['home']}, Guest: {booking['guest_name']}, Check-in: {booking['check_in']}, Check-out: {booking['check_out']}, Access Code: {booking['access_code']}")

def process_bookings_for_days(client, days):
    current_time = datetime.now()
    end_time = current_time + timedelta(days=days)

    for home in HOMES:
        bookings = fetch_airbnb_bookings(home['ical_url'])
        for booking in bookings:
            check_in = datetime.combine(booking['check_in'], datetime.min.time())
            check_out = datetime.combine(booking['check_out'], datetime.min.time())
            check_in = check_in.replace(hour=int(home['check_in_time'].split(':')[0]), minute=int(home['check_in_time'].split(':')[1]))
            check_out = check_out.replace(hour=int(home['check_out_time'].split(':')[0]), minute=int(home['check_out_time'].split(':')[1]))
            if current_time <= check_in <= end_time:
                create_access_code(client, home['lock_device_mac'], booking['guest_phone_last4'], check_in, check_out)

def encrypt_access_code(client, access_code: str) -> str:
    secret = client.locks._ford_client().get_crypt_secret()["secret"]
    iv = bytes.fromhex(client.locks._ford_client().WYZE_FORD_IV_HEX)
    if len(iv) != 16:
        raise ValueError("Incorrect IV length (it must be 16 bytes long)")
    hashed_secret = MD5Hasher().hash(secret)
    encrypted_access_code = CBCEncryptor(iv).encrypt(hashed_secret, access_code.encode())
    return encrypted_access_code.hex()

def create_access_code(client, device_mac, guest_phone_last4, check_in, check_out):
    access_code = str(guest_phone_last4)
    print(f"DEBUG: Access code before validation: {access_code}")  # Debug print
    days_stay = (check_out - check_in).days
    name = f"{check_in.strftime('%a')}-{days_stay}days"

    permission = LockKeyPermission(can_unlock=True, can_lock=True)
    periodicity = LockKeyPeriodicity(
        begin=check_in.strftime("%H%M%S"),
        end=check_out.strftime("%H%M%S"),
        valid_days=[0, 1, 2, 3, 4, 5, 6]
    )

    try:
        # Validate access_code as a string
        if not re.match(r'^\d{4,8}$', access_code):
            raise ValueError("Access code must be a 4-8 digit number")

        # Encrypt the access code
        encrypted_access_code = encrypt_access_code(client, access_code)

        response = client.locks.create_access_code(
            device_mac=device_mac,
            access_code=encrypted_access_code,
            name=name,
            permission=permission,
            periodicity=periodicity
        )
        #send email notification
        sendEmail(home=device_mac, lock=access_code, check_in=check_in, check_out=check_out)
        print(f"Access code {access_code} created for {name} in {device_mac}")
    except WyzeApiError as e:
        print(f"Failed to create access code for {name} in {device_mac}: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except WyzeRequestError as e:
        print(f"Error retrieving encryption secret: {e}")
    except Exception as e:
        print(f"Unexpected error while creating access code for {name} with data {access_code}: {e}")

def delete_access_codes(client, device_mac, check_out_time):
    keys = client.locks.get_keys(device_mac=device_mac)
    for key in keys:
        if key.name.endswith(f"days") and datetime.strptime(key.periodicity.end_time, "%Y-%m-%dT%H:%M:%S") <= check_out_time:
            try:
                client.locks.delete_access_code(
                    device_mac=device_mac,
                    access_code_id=key.id
                )
                print(f"Access code {key.id} deleted from {device_mac}")
            except WyzeApiError as e:
                print(f"Failed to delete access code {key.id} from {device_mac}: {e}")

def process_bookings(client):
    for home in HOMES:
        bookings = fetch_airbnb_bookings(home['ical_url'])
        for booking in bookings:
            check_in = booking['check_in'].replace(hour=int(home['check_in_time'].split(':')[0]), minute=int(home['check_in_time'].split(':')[1]))
            check_out = booking['check_out'].replace(hour=int(home['check_out_time'].split(':')[0]), minute=int(home['check_out_time'].split(':')[1]))
            create_access_code(client, home['lock_device_mac'], booking['guest_phone_last4'], check_in, check_out)

def schedule_cleanup_jobs(client):
    for home in HOMES:
        schedule_time = home['check_out_time']
        schedule.every().day.at(schedule_time).do(cleanup_access_codes_for_home, client, home)

def cleanup_access_codes_for_home(client, home):
    current_time = datetime.now().replace(hour=int(home['check_out_time'].split(':')[0]), minute=int(home['check_out_time'].split(':')[1]), second=0, microsecond=0)
    delete_access_codes(client, home['lock_device_mac'], current_time)

# Schedule tasks
def schedule_tasks(client):
    schedule.every(15).minutes.do(process_bookings, client)
    schedule.every().day.at("00:00").do(lambda: list_upcoming_bookings(client))  # Schedule listing of upcoming bookings at midnight daily
    schedule_cleanup_jobs(client)

def main():
    parser = argparse.ArgumentParser(description="Wyze Lock Airbnb Automation Script")
    parser.add_argument('--list-upcoming', action='store_true', help="List upcoming bookings for the next 7 days")
    parser.add_argument('--set-days', type=int, help="Set access codes for bookings in the next specified number of days")
    parser.add_argument('--testemail', action='store_true', help="Send a test email to verify email configuration")
    args = parser.parse_args()

    client = get_client()

    if args.testemail:
        # Define the test email details
        test_email = os.getenv('MAIL_TO')
        test_subject = "Test Email from Wyze Lock Airbnb Script"
        test_body = "This is a test email to verify the email configuration."
        sendTestEmail(test_email, test_subject, test_body)
        return  # Use return to exit the function after sending test email
    elif args.list_upcoming:
        list_upcoming_bookings(client)
    elif args.set_days:
        process_bookings_for_days(client, args.set_days)
    else:
        schedule_tasks(client)
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    main()
