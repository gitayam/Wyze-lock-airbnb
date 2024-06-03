#readme.md
# Wyze-lock-airbnb

This project automates the management of Wyze lock access codes based on Airbnb bookings. It fetches booking information from Airbnb calendars and sets or deletes lock access codes accordingly.

## Prerequisites

- Python 3.x
- Access to the Wyze SDK
- Access to the Airbnb iCal URLs

## Installation

1. **Clone the Repository**
   ```bash
   git clone git@github.com:gitayam/Wyze-lock-airbnb.git
   cd Wyze-lock-airbnb
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
   - Copy the `.env` template and edit it with your credentials
   ```bash
   cp .env-template .env
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
   - Add `.env` to `.gitignore`
     ```bash
     echo ".env" >> .gitignore
     echo "venv" >> .gitignore
     ```

## Running the Script

1. **Run the Script**
   ```bash
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
   ```bash
   sudo systemctl enable wyze-lock-airbnb.service
   sudo systemctl start wyze-lock-airbnb.service
   ```
**MacOS:**
   ```bash
   sudo launchctl load /etc/systemd/system/wyze-lock-airbnb.service
   sudo launchctl start wyze-lock-airbnb.service
   ```
**Windows:**
   ```cmd
   sc create wyze-lock-airbnb binPath= "C:\path\to\python.exe C:\path\to\wyze-lock-airbnb.py" start= auto
   sc start wyze-lock-airbnb
   ```
This setup ensures that your script runs in the background, automatically managing the lock access codes based on Airbnb bookings.
