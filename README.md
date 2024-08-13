# PROJECT OVERVIEW #
This Python script tracks job application emails in your Gmail account, extracts relevant information such as company names, email subjects, and dates, and saves the data to a CSV file.

# Features #
 - Connects to Gmail via API.
 - Extracts key details from job-related emails.
 - Outputs the data into a CSV file.
 - Logs actions and errors for easy debugging.

# Requirements #
 - Python 3.6 or higher
 - A Google Cloud account with the Gmail API enabled

 # Setup Instructions In Terminal #
  1. Clone repository:
    - git clone https://github.com/mprojr/Job-Application-Tracker.git
  cd Job-Application-Tracker

  2. Create virtual environment:
    - python3 -m venv myenv

  3. Activate virtual enviroment
    - WINDOWS: myenv\Scripts\activate
    - MacOS/Linus: source myenv/bin/activate

  4. Install Packages Needed
    - pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    - Enable Gmail API in Google Cloud
    - Create OAuth 2.0 credentials
    - Download 'credentials.json' (Given by google)
    - cp config.example.json config.json (replace example files with your expected files, remove .example from file name.)
    - Update config.json with your specific details.

  5. Run the Script
    - python3 email_tracker.py
    - make sure to authenticate with your google account

 # View Output #
   - You will recieve an output csv file, and a logs file that'll give you information on extracted data, alongside logs and errors

 # Troubleshooting #
   - Authentication issues? Delete 'token.pickle' and re-run.
   - No data found? Adjust 'search_emails()' function.

