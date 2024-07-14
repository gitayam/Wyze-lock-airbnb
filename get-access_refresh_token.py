import requests
import os
import pyotp
import argparse
import schedule
from dotenv import load_dotenv, set_key
from datetime import datetime, timedelta

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

def get_tokens(email, password, api_key, key_id):
    login_url = 'https://auth-prod.api.wyze.com/api/user/login'
    
    payload = {
        "email": email,
        "password": password
    }
    headers = {
        'Keyid': key_id,
        'Apikey': api_key,
        'Content-Type': 'application/json'
    }

    print("Debug Info: Sending request to Wyze API")
    print(f"URL: {login_url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")

    response = requests.post(login_url, json=payload, headers=headers)
    
    print("Debug Info: Response received")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    response.raise_for_status()

    tokens = response.json()
    print("Access Token: ", tokens['access_token'])
    print("Refresh Token: ", tokens['refresh_token'])
    return tokens['access_token'], tokens['refresh_token']

def get_tokens_with_mfa(email, password, api_key, key_id, totp_key):
    login_url = 'https://auth-prod.api.wyze.com/api/user/login'
    
    # Generate the TOTP code using the shared secret
    totp = pyotp.TOTP(totp_key)
    totp_code = totp.now()
    
    payload = {
        "email": email,
        "password": password,
        "mfa_type": "TotpVerificationCode",
        "verification_code": totp_code
    }
    headers = {
        'Keyid': key_id,
        'Apikey': api_key,
        'Content-Type': 'application/json'
    }

    print("Debug Info: Sending request to Wyze API with MFA")
    print(f"URL: {login_url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")

    response = requests.post(login_url, json=payload, headers=headers)
    
    print("Debug Info: Response received")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    response.raise_for_status()

    tokens = response.json()
    print("Access Token: ", tokens['access_token'])
    print("Refresh Token: ", tokens['refresh_token'])
    return tokens['access_token'], tokens['refresh_token']

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
        update_env_file(new_access_token, new_refresh_token)
        return new_access_token, new_refresh_token
    else:
        raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

def update_env_file(access_token, refresh_token):
    set_key(ENV_FILE_PATH, 'WYZE_ACCESS_TOKEN', access_token)
    set_key(ENV_FILE_PATH, 'WYZE_REFRESH_TOKEN', refresh_token)
    print("Access and refresh tokens have been saved to the .env file.")

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

    required_vars = ['WYZE_EMAIL', 'WYZE_PASSWORD', 'WYZE_API_KEY', 'WYZE_KEY_ID']
    if args.mfa:
        required_vars.append('WYZE_TOTP_KEY')

    if not check_env_variables(required_vars):
        return

    try:
        if args.mfa:
            access_token, refresh_token = get_tokens_with_mfa(WYZE_EMAIL, WYZE_PASSWORD, WYZE_API_KEY, WYZE_KEY_ID, WYZE_TOTP_KEY)
        else:
            access_token, refresh_token = get_tokens(WYZE_EMAIL, WYZE_PASSWORD, WYZE_API_KEY, WYZE_KEY_ID)
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
        update_env_file(access_token, refresh_token)

        # Schedule token refresh every 30 minutes
        schedule.every(30).minutes.do(refresh_access_token, refresh_token=refresh_token)

        # Main loop to keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")

if __name__ == "__main__":
    main()