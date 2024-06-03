#wyze-lock-airbnb.py
import requests
from icalendar import Calendar
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError
from wyze_sdk.models.devices.locks import LockKey, LockKeyPermission, LockKeyPeriodicity
import re
import schedule
import time
from datetime import datetime, timedelta  # Added timedelta
from dotenv import load_dotenv
import os
import argparse  # Added argparse for command-line arguments

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

def list_upcoming_bookings(days=7):
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


def process_bookings_for_days(days):
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
                create_access_code(home['lock_device_mac'], booking['guest_phone_last4'], check_in, check_out)


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

def delete_access_codes(device_mac, check_out_time):
    keys = client.devices.locks.get_keys(device_mac=device_mac)
    for key in keys:
        if key.name.endswith(f"days") and datetime.strptime(key.periodicity.end_time, "%Y-%m-%dT%H:%M:%S") <= check_out_time:
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

def schedule_cleanup_jobs():
    for home in HOMES:
        # Schedule cleanup at checkout time
        schedule_time = home['check_out_time']
        schedule.every().day.at(schedule_time).do(cleanup_access_codes_for_home, home)

def cleanup_access_codes_for_home(home):
    current_time = datetime.now().replace(hour=int(home['check_out_time'].split(':')[0]), minute=int(home['check_out_time'].split(':')[1]), second=0, microsecond=0)
    delete_access_codes(home['lock_device_mac'], current_time)
    
def process_bookings_for_days(days):
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
                create_access_code(home['lock_device_mac'], booking['guest_phone_last4'], check_in, check_out)

# Schedule tasks
schedule.every(15).minutes.do(process_bookings)
schedule.every().day.at("00:00").do(list_upcoming_bookings)  # Schedule listing of upcoming bookings at midnight daily
schedule_cleanup_jobs()

def main():
    parser = argparse.ArgumentParser(description="Wyze Lock Airbnb Automation Script")
    parser.add_argument('--list-upcoming', action='store_true', help="List upcoming bookings for the next 7 days")
    parser.add_argument('--set-days', type=int, help="Set access codes for bookings in the next specified number of days")
    args = parser.parse_args()

    if args.list_upcoming:
        list_upcoming_bookings()
    elif args.set_days:
        process_bookings_for_days(args.set_days)
    else:
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main()
