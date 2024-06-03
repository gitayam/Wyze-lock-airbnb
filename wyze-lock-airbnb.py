#wyze-lock-airbnb.py
import requests
from icalendar import Calendar
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError
from wyze_sdk.models.devices import LockKeyPermission, LockKeyPeriodicity
import re
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Constants
HOMES = [
    {
        'name': 'Home 1',
        'ical_url': os.getenv('HOME_1_ICAL_URL'),
        'lock_device_mac': os.getenv('HOME_1_LOCK_DEVICE_MAC'),
        'check_in_time': os.getenv('HOME_1_CHECK_IN_TIME'),
        'check_out_time': os.getenv('HOME_1_CHECK_OUT_TIME')
    },
    {
        'name': 'Home 2',
        'ical_url': os.getenv('HOME_2_ICAL_URL'),
        'lock_device_mac': os.getenv('HOME_2_LOCK_DEVICE_MAC'),
        'check_in_time': os.getenv('HOME_2_CHECK_IN_TIME'),
        'check_out_time': os.getenv('HOME_2_CHECK_OUT_TIME')
    }
]
WYZE_ACCESS_TOKEN = os.getenv('WYZE_ACCESS_TOKEN')

# Initialize Wyze Client
client = Client(token=WYZE_ACCESS_TOKEN)

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
                bookings.append({
                    'check_in': component.get('DTSTART').dt,
                    'check_out': component.get('DTEND').dt,
                    'guest_phone_last4': phone_last4
                })
    return bookings

def create_access_code(device_mac, guest_phone_last4, check_in, check_out):
    access_code = guest_phone_last4
    # Custom name format: "DayOfWeek-#days"
    days_stay = (check_out - check_in).days
    name = f"{check_in.strftime('%a')}-{days_stay}days"
    
    permission = LockKeyPermission(can_unlock=True, can_lock=True)
    periodicity = LockKeyPeriodicity(
        type="once",  # Valid for a single time period
        start_time=check_in.strftime("%Y-%m-%dT%H:%M:%S"),  # ISO 8601 format
        end_time=check_out.strftime("%Y-%m-%dT%H:%M:%S")    # ISO 8601 format
    )
    
    try:
        response = client.devices.locks.create_access_code(
            device_mac=device_mac,
            access_code=access_code,
            name=name,
            permission=permission,
            periodicity=periodicity
        )
        print(f"Access code {access_code} created for {name} in {device_mac}")
    except WyzeApiError as e:
        print(f"Failed to create access code for {name} in {device_mac}: {e}")

def delete_access_codes(device_mac, check_out_date):
    keys = client.devices.locks.get_keys(device_mac=device_mac)
    for key in keys:
        if key.name.endswith(f"days") and datetime.strptime(key.periodicity.end_time, "%Y-%m-%dT%H:%M:%S") < check_out_date:
            try:
                client.devices.locks.delete_access_code(
                    device_mac=device_mac,
                    access_code_id=key.id
                )
                print(f"Access code {key.id} deleted from {device_mac}")
            except WyzeApiError as e:
                print(f"Failed to delete access code {key.id} from {device_mac}: {e}")

def process_bookings():
    for home in HOMES:
        bookings = fetch_airbnb_bookings(home['ical_url'])
        
        for booking in bookings:
            check_in = booking['check_in'].replace(hour=int(home['check_in_time'].split(':')[0]), minute=int(home['check_in_time'].split(':')[1]))
            check_out = booking['check_out'].replace(hour=int(home['check_out_time'].split(':')[0]), minute=int(home['check_out_time'].split(':')[1]))
            
            create_access_code(
                home['lock_device_mac'], 
                booking['guest_phone_last4'], 
                check_in, 
                check_out
            )

def cleanup_access_codes():
    current_time = datetime.now()
    for home in HOMES:
        delete_access_codes(home['lock_device_mac'], current_time)

# Schedule tasks
schedule.every(1).hour.do(process_bookings)
schedule.every().day.at("23:59").do(cleanup_access_codes)

def main():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
