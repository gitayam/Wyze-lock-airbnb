import requests
import os
from dotenv import load_dotenv, set_key

# Load environment variables from .env file
load_dotenv()

# Constants
WYZE_EMAIL = os.getenv('WYZE_EMAIL')
WYZE_PASSWORD = os.getenv('WYZE_PASSWORD')
WYZE_API_KEY = os.getenv('WYZE_API_KEY')
WYZE_KEY_ID = os.getenv('WYZE_KEY_ID')
WYZE_TOTP_KEY = os.getenv('WYZE_TOTP_KEY')
ENV_FILE_PATH = '.env'

# Check if all necessary environment variables are set
def check_env_variables():
    missing_vars = [var for var in ['WYZE_EMAIL', 'WYZE_PASSWORD', 'WYZE_API_KEY', 'WYZE_KEY_ID', 'WYZE_TOTP_KEY'] if not os.getenv(var)]
    if missing_vars:
        print(f"Please ensure the following environment variables are set in the .env file: {', '.join(missing_vars)}")
        return False
    return True

def get_tokens(email, password, api_key, key_id, totp_key):
    login_url = 'https://auth-prod.api.wyze.com/api/user/login'
    payload = {
        "email": email,
        "password": password,
        "totp_key": totp_key
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
    return tokens['access_token'], tokens['refresh_token']

def update_env_file(access_token, refresh_token):
    set_key(ENV_FILE_PATH, 'WYZE_ACCESS_TOKEN', access_token)
    set_key(ENV_FILE_PATH, 'WYZE_REFRESH_TOKEN', refresh_token)
    print("Access and refresh tokens have been saved to the .env file.")

def main():
    if not check_env_variables():
        return

    try:
        access_token, refresh_token = get_tokens(WYZE_EMAIL, WYZE_PASSWORD, WYZE_API_KEY, WYZE_KEY_ID, WYZE_TOTP_KEY)
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
        update_env_file(access_token, refresh_token)
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")

if __name__ == "__main__":
    main()