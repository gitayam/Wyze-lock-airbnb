#readme.md
# Wyze-lock-airbnb
## Prerequisites

- Python 3.x
- `requests` library
- `python-dotenv` library
- Access to the Authentik API

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/irregularchat/authentik-account-creation.git
   cd authentik-user-creation
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   - Copy the .env template, gitignore it so that it doesn't sync and edit
   ```bash
   cp .env-template .env
   echo ".env" >> .gitignore
   echo "venv" >> .gitignore

   nano .env
   ```
   - Or create a `.env` file in the project directory and add the following:
     ```env
    WYZE_ACCESS_TOKEN=your_wyze_access_token
    
    HOME_1_ICAL_URL=your_home_1_airbnb_ical_url
    HOME_1_LOCK_DEVICE_MAC=your_home_1_lock_device_mac
    HOME_1_CHECK_IN_TIME=16:00
    HOME_1_CHECK_OUT_TIME=11:00

    HOME_2_ICAL_URL=your_home_2_airbnb_ical_url
    HOME_2_LOCK_DEVICE_MAC=your_home_2_lock_device_mac
    HOME_2_CHECK_IN_TIME=15:00
    HOME_2_CHECK_OUT_TIME=10:00
      ```
     - add to gitignore

    ```bash
    echo ".env" >> .gitignore
    ```


