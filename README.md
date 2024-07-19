# Wyze-lock-airbnb

This project automates the management of Wyze lock access codes based on Airbnb bookings. It fetches booking information from Airbnb calendars and sets or deletes lock access codes accordingly.

#NOTE: Still in active development. 

## Roadmap
- [x] Take Last 4 from Airbnb Calendar Event
- [x] Add Email SMTP to send email confirmations
- [ ] Keypad working (working, currently have an [issue](https://github.com/shauntarves/wyze-sdk/issues/184))
- [ ] Constant running checking every x min between a time range (checkin time)
- [ ] Build into a website for non cli use
- [ ] Work with other brands
- [ ] Check for Deleted / Canceled Stays and Delete Code
## Prerequisites

- Python 3.x
- Access to the Wyze SDK
- Access to the Airbnb iCal URLs

## Installation

1. **Clone the Repository**
   ```shell
   git clone git@github.com:gitayam/Wyze-lock-airbnb.git
   cd Wyze-lock-airbnb
   ```

2. **Create a Virtual Environment**
   ```shell
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```shell
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   - Copy the `.env` template and edit it with your credentials
   ```shell
   cp .env-template .env
   nano .env
   ```
   - Or create a `.env` file in the project directory and add the following:
  ```env
#.env-template
WYZE_EMAIL=your_email@example.com # required the first time to obtain the access token
WYZE_PASSWORD=your_password # required the first time to obtain the access token
WYZE_TOTP_KEY=your_totp_key # required to login when account has MFA enabled
WYZE_API_KEY=your_api_key
WYZE_KEY_ID=your_key_id
WYZE_ACCESS_TOKEN=your_access_token # provided by the script
WYZE_REFRESH_TOKEN=your_refresh_token # provided by the script

HOME_1_NAME="Name House"
HOME_1_ICAL_URL=your_home_1_airbnb_ical_url
HOME_1_LOCK_DEVICE_MAC=your_home_1_lock_device_mac
HOME_1_KEYPAD_SERIAL_NUMBER=your_home_1_keypad_device_mac
HOME_1_CHECK_IN_TIME=16:00
HOME_1_CHECK_OUT_TIME=11:00

HOME_1_NAME="Name House"
HOME_2_ICAL_URL=your_home_2_airbnb_ical_url
HOME_2_LOCK_DEVICE_MAC=your_home_2_lock_device_mac
HOME_2_KEYPAD_SERIAL_NUMBER=your_home_2_keypad_device_mac
HOME_2_CHECK_IN_TIME=15:00
HOME_2_CHECK_OUT_TIME=10:00

#SMTP SERVERS
SMTP_HOST=smtp.host.com
SMTP_PORT=587
SMTP_USERNAME=USERNAME_HERE
SMTP_PASSWORD=PASSWORD_HERE
SMTP_FROM=EMAIL_HERE
MAIL_TO=EMAIL_HERE
MAIL_CC=EMAIL_CC_HERE

  ```

5. **Obtain Access and Refresh Tokens**
   - Run the script to get your access and refresh tokens. This will automatically append them to your `.env` file.
   ```shell
   python get-access_refresh_token.py
   ```

## Running the Script

1. **Run the Script**
   ```shell
   python wyze-lock-airbnb.py
   ```

This will start the script, which will run continuously, checking for new bookings every 15 minutes and cleaning up access codes at the specified checkout times.

## Setting Up as a Service

To run the script continuously on a server, you can set it up as a service using `systemd`:

1. **Create a `systemd` Service File**

   Create a file named `wyze-lock-airbnb.service` in `/etc/systemd/system/` with the following content:

   ```ini
   [Unit]
   Description=Wyze Lock Airbnb Sync Service
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/your/wyze-lock-airbnb.py
   WorkingDirectory=/path/to/your/
   EnvironmentFile=/path/to/your/.env
   Restart=always
   User=your_user
   Group=your_group

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and Start the Service**

**Linux:**
   ```shell
   sudo systemctl enable wyze-lock-airbnb.service
   sudo systemctl start wyze-lock-airbnb.service
   ```
**MacOS:**
   ```shell
   sudo launchctl load /etc/systemd/system/wyze-lock-airbnb.service
   sudo launchctl start wyze-lock-airbnb.service
   ```
**Windows:**
   ```cmd
   sc create wyze-lock-airbnb binPath= "C:\path\to\python.exe C:\path\to\wyze-lock-airbnb.py" start= auto
   sc start wyze-lock-airbnb
   ```
This setup ensures that your script runs in the background, automatically managing the lock access codes based on Airbnb bookings.
