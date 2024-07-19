import os
import time
import requests
import argparse
import logging
from dotenv import load_dotenv
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

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

def _get_lock_devices(client):
    ford_client = client._service_client(FordServiceClient, token=client._token, base_url=client._base_url)
    return ford_client.get_user_device().data

def list_lock_devices(client):
    try:
        lock_devices = _get_lock_devices(client)
        logging.info("Lock devices retrieved successfully")
        for device in lock_devices:
            try:
                print(f"Device: {device.nickname}")
                for attr in dir(device):
                    if not attr.startswith('_') and not callable(getattr(device, attr)):
                        try:
                            print(f"  {attr}: {getattr(device, attr)}")
                        except AttributeError as ae:
                            print(f"  {attr}: Attribute not accessible - {str(ae)}")
                        except Exception as e:
                            print(f"  {attr}: Unexpected error - {str(e)}")
                print()
            except Exception as device_error:
                logging.error(f"Error processing device: {device}. Error: {device_error}")
    except WyzeApiError as e:
        logging.error(f"Failed to list lock devices: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while listing lock devices: {e}")

def main():
    parser = argparse.ArgumentParser(description="Wyze Lock Device List Script")
    args = parser.parse_args()

    try:
        client = get_client()
        list_lock_devices(client)
    except Exception as e:
        logging.error(f"Script failed: {e}")

if __name__ == "__main__":
    main()
