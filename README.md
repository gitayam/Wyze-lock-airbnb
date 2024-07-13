# Wyze-lock-airbnb

This project automates the management of Wyze lock access codes based on Airbnb bookings. It fetches booking information from Airbnb calendars and sets or deletes lock access codes accordingly.

#NOTE: Still in active development. 

## Roadmap
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
  WYZE_EMAIL=your_email@example.com
  WYZE_PASSWORD=your_password
  WYZE_API_KEY=your_api_key
  WYZE_KEY_ID=your_key_id
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
