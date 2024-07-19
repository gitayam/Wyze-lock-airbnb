import os
import time
import requests
from dotenv import load_dotenv
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

# Load environment variables from .env file
load_dotenv()

# Constants

HOME_1_LOCK_DEVICE_MAC = os.getenv('HOME_1_LOCK_DEVICE_MAC')
HOME_2_LOCK_DEVICE_MAC = os.getenv('HOME_2_LOCK_DEVICE_MAC')
WYZE_ACCESS_TOKEN = os.getenv('WYZE_ACCESS_TOKEN')
WYZE_REFRESH_TOKEN = os.getenv('WYZE_REFRESH_TOKEN')

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
        os.environ['WYZE_ACCESS_TOKEN'] = new_access_token
        os.environ['WYZE_REFRESH_TOKEN'] = new_refresh_token
        return new_access_token, new_refresh_token
    else:
        raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

# Function to get the client
def get_client():
    global WYZE_ACCESS_TOKEN, WYZE_REFRESH_TOKEN
    try:
        client = Client(token=WYZE_ACCESS_TOKEN)
        client.devices_list()
    except WyzeApiError as e:
        if "AccessTokenError" in str(e) or "access token expired" in str(e):
            print("Access token expired, refreshing...")
            try:
                WYZE_ACCESS_TOKEN, WYZE_REFRESH_TOKEN = refresh_access_token(WYZE_REFRESH_TOKEN)
                client = Client(token=WYZE_ACCESS_TOKEN)
            except Exception as refresh_error:
                print(f"Failed to refresh access token: {refresh_error}")
                raise e
        else:
            raise e
    return client

# Function to list out the devices and identify keypads
def list_devices(client):
    try:
        devices = client.devices_list()
        print("DEBUG: Listing all devices:")
        for device in devices:
            device_info = device.__dict__  # Get device attributes
            if 'product_model' in device_info:
                print(f"Device name: {device_info.get('nickname', 'Unknown')}, MAC: {device_info.get('mac', 'Unknown')}, Model: {device_info.get('product_model', 'Unknown')}")
                if 'keypad' in device_info['product_model'].lower():
                    print(f"Keypad found: {device_info.get('nickname', 'Unknown')} with MAC {device_info.get('mac', 'Unknown')}")
            else:
                print(f"Unknown device type detected: {device_info}")
    except Exception as e:
        print(f"Unexpected error while listing devices: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception args: {e.args}")

# Function to check and activate keypads
def check_and_activate_keypads(client, lock_mac):
    try:
        lock_info = client.locks.info(device_mac=lock_mac)
        if lock_info and lock_info.keypad:
            print(f"Keypad is already enabled for lock {lock_mac}.")
        else:
            print(f"No keypad associated with lock {lock_mac}. Trying to activate...")
            # Code to activate keypad if the function exists in the SDK or you have an API endpoint to do it
            # Example: client.locks.activate_keypad(lock_mac=lock_mac)
    except Exception as e:
        print(f"Error checking/activating keypad for lock with MAC {lock_mac}: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception args: {e.args}")

def main():
    client = get_client()
    list_devices(client)
    
    # Assuming you have a function to get the lock MACs
    lock_macs = [os.getenv('HOME_1_LOCK_DEVICE_MAC'), os.getenv('HOME_2_LOCK_DEVICE_MAC')]
    for lock_mac in lock_macs:
        check_and_activate_keypads(client, lock_mac)

if __name__ == "__main__":
    main()
