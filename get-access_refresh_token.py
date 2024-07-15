import os
import pyotp
import argparse
import schedule
import time
from dotenv import load_dotenv, set_key
from datetime import datetime, timedelta
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

# Load environment variables from .env file
load_dotenv()

# Constants
WYZE_EMAIL = os.getenv('WYZE_EMAIL')
WYZE_PASSWORD = os.getenv('WYZE_PASSWORD')
WYZE_API_KEY = os.getenv('WYZE_API_KEY')
WYZE_KEY_ID = os.getenv('WYZE_KEY_ID')
WYZE_TOTP_KEY = os.getenv('WYZE_TOTP_KEY')
WYZE_ACCESS_TOKEN = os.getenv('WYZE_ACCESS_TOKEN')
WYZE_REFRESH_TOKEN = os.getenv('WYZE_REFRESH_TOKEN')
ENV_FILE_PATH = '.env'

# Check if all necessary environment variables are set
def check_env_variables(required_vars):
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Please ensure the following environment variables are set in the .env file: {', '.join(missing_vars)}")
        return False
    return True

def authenticate_with_sdk(email, password, key_id=None, api_key=None, totp_key=None):
    client = Client()
    try:
        if totp_key:
            response = client.login(email=email, password=password, key_id=key_id, api_key=api_key, totp_key=totp_key)
        else:
            response = client.login(email=email, password=password, key_id=key_id, api_key=api_key)

        access_token = response['access_token']
        refresh_token = response['refresh_token']
        print("Access Token: ", access_token)
        print("Refresh Token: ", refresh_token)
        return access_token, refresh_token
    except WyzeApiError as e:
        print(f"Authentication failed: {e}")
        raise

def refresh_access_token(refresh_token):
    client = Client(refresh_token=refresh_token)
    try:
        response = client.refresh_token()
        new_access_token = response['access_token']
        new_refresh_token = response['refresh_token']
        update_env_file(new_access_token, new_refresh_token)
        return new_access_token, new_refresh_token
    except WyzeApiError as e:
        print(f"Failed to refresh access token: {e}")
        raise

def update_env_file(access_token, refresh_token):
    set_key(ENV_FILE_PATH, 'WYZE_ACCESS_TOKEN', access_token)
    set_key(ENV_FILE_PATH, 'WYZE_REFRESH_TOKEN', refresh_token)
    print("Access and refresh tokens have been saved to the .env file.")
    # exit function after this point to avoid infinite loop
    exit()

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

def main():
    parser = argparse.ArgumentParser(description="Wyze Token Retriever")
    parser.add_argument('--mfa', action='store_true', help="Use MFA for authentication")
    args = parser.parse_args()

    required_vars = ['WYZE_EMAIL', 'WYZE_PASSWORD']
    if args.mfa:
        required_vars.append('WYZE_TOTP_KEY')

    if not check_env_variables(required_vars):
        return

    try:
        if args.mfa:
            access_token, refresh_token = authenticate_with_sdk(WYZE_EMAIL, WYZE_PASSWORD, WYZE_KEY_ID, WYZE_API_KEY, WYZE_TOTP_KEY)
        else:
            access_token, refresh_token = authenticate_with_sdk(WYZE_EMAIL, WYZE_PASSWORD, WYZE_KEY_ID, WYZE_API_KEY)
        
        update_env_file(access_token, refresh_token)

        # Schedule token refresh every 30 minutes
        schedule.every(30).minutes.do(refresh_access_token, refresh_token=refresh_token)

        # Main loop to keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)
    except WyzeApiError as err:
        print(f"API error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")

if __name__ == "__main__":
    main()