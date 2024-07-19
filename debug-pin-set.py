import os
import re
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError, WyzeRequestError
from wyze_sdk.models.devices.locks import LockKeyPermission, LockKeyPeriodicity, LockKeyPermissionType
from wyze_sdk.signature import CBCEncryptor, MD5Hasher

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

# Function to list out the locks for debugging
def list_locks(client):
    try:
        locks = client.locks.list()
        print("DEBUG: Listing all locks:")
        for lock in locks:
            print(f"Lock name: {lock.nickname}, MAC: {lock.mac}")
    except Exception as e:
        print(f"Unexpected error while listing locks: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception args: {e.args}")

# Function to list out the keypads for debugging
def list_keypads(client):
    try:
        devices = client.devices_list()
        print("DEBUG: Listing all keypads:")
        for device in devices:
            # Adjust the condition according to the actual product model of your keypads
            if hasattr(device, 'product_model') and device.product_model == 'Keypad':
                print(f"Keypad name: {device.nickname}, MAC: {device.mac}")
    except Exception as e:
        print(f"Unexpected error while listing keypads: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception args: {e.args}")

def create_temp_access_code(client, device_mac, access_code, check_in, check_out):
    print(f"DEBUG: Access code before validation: {access_code}")
    days_stay = (check_out - check_in).days
    name = f"{check_in.strftime('%a')}-{days_stay}days"

    permission = LockKeyPermission(type=LockKeyPermissionType.ALWAYS, can_unlock=True, can_lock=True)
    periodicity = LockKeyPeriodicity(
        begin=check_in.strftime("%H%M%S"),
        end=check_out.strftime("%H%M%S"),
        valid_days=[0, 1, 2, 3, 4, 5, 6]
    )

    try:
        # Extra debug information
        print(f"DEBUG: device_mac: {device_mac}")
        print(f"DEBUG: access_code: {access_code}")
        print(f"DEBUG: name: {name}")
        print(f"DEBUG: permission: {permission}")
        print(f"DEBUG: periodicity: {periodicity}")

        # Validate access code
        if not re.match(r'^\d{4,8}$', access_code):
            raise ValueError("Access code must be a 4-8 digit number")

        # Encrypt access code
        secret = client.locks._ford_client().get_crypt_secret()["secret"]
        encrypted_code = CBCEncryptor(client.locks._ford_client().WYZE_FORD_IV_HEX).encrypt(MD5Hasher().hash(secret), access_code.encode()).hex()
        print(f"DEBUG: Encrypted access code: {encrypted_code}")

        # Attempting to create access code
        response = client.locks.create_access_code(
            device_mac=device_mac,
            access_code=encrypted_code,
            name=name,
            permission=permission,
            periodicity=periodicity
        )
        print(f"Access code {access_code} created for {name} in {device_mac}")
    except WyzeRequestError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Unexpected error while creating access code for {name} with data {access_code}: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception args: {e.args}")

def main():
    # Debug information for environment variables
    print(f"DEBUG: HOME_1_LOCK_DEVICE_MAC: {HOME_1_LOCK_DEVICE_MAC}")
    print(f"DEBUG: HOME_2_LOCK_DEVICE_MAC: {HOME_2_LOCK_DEVICE_MAC}")
    print(f"DEBUG: WYZE_ACCESS_TOKEN: {WYZE_ACCESS_TOKEN[:10]}...")  # Print partial token for security
    print(f"DEBUG: WYZE_REFRESH_TOKEN: {WYZE_REFRESH_TOKEN[:10]}...")  # Print partial token for security

    client = get_client()

    # List locks and keypads for debugging
    list_locks(client)
    list_keypads(client)

    access_code = "1238"
    check_in = datetime.now()
    check_out = check_in + timedelta(days=1)

    create_temp_access_code(client, HOME_1_LOCK_DEVICE_MAC, access_code, check_in, check_out)

if __name__ == "__main__":
    main()
