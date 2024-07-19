import os
import time
import argparse
import logging
import requests
from dotenv import load_dotenv
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError
from wyze_sdk.models.devices.locks import LockKeyPermission, LockKeyPermissionType

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

HOME_1_LOCK_DEVICE_MAC = os.getenv('HOME_1_LOCK_DEVICE_MAC')
HOME_2_LOCK_DEVICE_MAC = os.getenv('HOME_2_LOCK_DEVICE_MAC')
WYZE_ACCESS_TOKEN = os.getenv('WYZE_ACCESS_TOKEN')
WYZE_REFRESH_TOKEN = os.getenv('WYZE_REFRESH_TOKEN')

LOCK_MAC_ADDRESS = HOME_1_LOCK_DEVICE_MAC  # USING ONLY ONE FOR TESTING
ACCESS_CODE = "1234"  # Replace with desired access code
ACCESS_CODE_NAME = "Testtt"  # Replace with desired access code name
START_TIME = int(time.time()) * 1000  # Current time in milliseconds
END_TIME = START_TIME + 24 * 60 * 60 * 1000  # 24 hours from now in milliseconds

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

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        new_access_token = data['data']['access_token']
        new_refresh_token = data['data']['refresh_token']
        logging.info("Access token refreshed successfully")
        return new_access_token, new_refresh_token
    except requests.RequestException as e:
        logging.error(f"Failed to refresh token: {e}")
        raise

# Function to get the client
def get_client():
    global WYZE_ACCESS_TOKEN, WYZE_REFRESH_TOKEN
    try:
        client = Client(token=WYZE_ACCESS_TOKEN)
        # Test if the access token is valid
        client.devices_list()
        logging.info("Access token is valid")
    except WyzeApiError as e:
        if "AccessTokenError" in str(e) or "access token expired" in str(e):
            logging.warning("Access token expired, refreshing...")
            try:
                WYZE_ACCESS_TOKEN, WYZE_REFRESH_TOKEN = refresh_access_token(WYZE_REFRESH_TOKEN)
                os.environ['WYZE_ACCESS_TOKEN'] = WYZE_ACCESS_TOKEN
                os.environ['WYZE_REFRESH_TOKEN'] = WYZE_REFRESH_TOKEN
                client = Client(token=WYZE_ACCESS_TOKEN)
            except Exception as refresh_error:
                logging.error(f"Failed to refresh access token: {refresh_error}")
                raise e  # Re-raise the original error if refreshing fails
        else:
            logging.error(f"WyzeApiError: {e}")
            raise e  # Re-raise the original error if it's not an access token issue
    return client

def set_guest_access_code(client, lock_mac, access_code, code_name, start_time, end_time):
    try:
        # Fetch the lock device
        device = next((d for d in client.devices_list() if d.mac == lock_mac), None)
        if not device:
            logging.error(f"No device found with MAC address {lock_mac}")
            return

        # Check if the lock has a keypad and if it is enabled
        if not hasattr(device, 'keypad') or device.keypad is None:
            logging.error(f"The lock device {device.nickname} does not have a keypad.")
            return
        if not device.keypad.is_enabled:
            logging.error(f"The lock device {device.nickname} has a keypad, but it is not enabled.")
            return

        logging.info(f"Setting guest access code for device: {device.nickname}")

        permission = LockKeyPermission(
            type=LockKeyPermissionType.ALWAYS,
            begin=start_time,
            end=end_time
        )

        client.locks.create_access_code(
            device_mac=lock_mac,
            name=code_name,
            access_code=access_code,
            permission=permission
        )
        
        logging.info("Guest access code set successfully")
    except WyzeApiError as e:
        logging.error(f"Failed to set guest access code: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while setting guest access code: {e}")

def main():
    parser = argparse.ArgumentParser(description="Wyze Lock Guest Access Code Setter")
    args = parser.parse_args()

    try:
        client = get_client()
        set_guest_access_code(client, LOCK_MAC_ADDRESS, ACCESS_CODE, ACCESS_CODE_NAME, START_TIME, END_TIME)
    except Exception as e:
        logging.error(f"Script failed: {e}")

if __name__ == "__main__":
    main()
