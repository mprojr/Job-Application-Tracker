import os
import pickle
import re
import csv
import json
import logging
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Configuration settings
SCOPES = config['scopes']
CREDENTIALS_FILE = config['credentials_file']
TOKEN_FILE = config['token_file']
OUTPUT_FILE = config['output_file']

# Setup logging
logging.basicConfig(filename='email_tracker.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate_gmail():
    """Authenticate with Gmail API and return the service object."""
    try:
        creds = None
        # Load saved credentials from token.pickle if they exist
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        # If credentials are not valid or do not exist, authenticate and save new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Error during Gmail authentication: {e}")
        raise

def search_emails(service):
    """Search for emails in the user's Gmail inbox based on a query."""
    try:
        query = 'label:important (subject:(application OR submitted) OR body:(application OR submitted OR "Thank you for your interest"))'
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        return messages
    except Exception as e:
        logging.error(f"Error during email search: {e}")
        raise

def extract_company_name(from_header, snippet):
    """Extract the company name from the 'From' header or email snippet."""
    patterns = [
        r'at\s(\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)',
        r'from\s(\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)',
        r'application\sreceived\sfrom\s(\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)',
        r'interview\swith\s(\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)'
    ]
    company_name = None
    if from_header:
        company_name_match = re.search(r'[\w\.-]+@([\w\.-]+)', from_header)
        if company_name_match:
            domain = company_name_match.group(1).split('.')[0]
            company_name = domain.capitalize()

    if not company_name:
        for pattern in patterns:
            company_name_match = re.search(pattern, snippet)
            if company_name_match:
                company_name = company_name_match.group(1)
                break
    return company_name

def get_header(headers, name, default=''):
    """Utility function to get a header value by name, with a default fallback."""
    return next((header['value'] for header in headers if header['name'] == name), default)

def extract_email_metadata(headers, snippet):
    """Extract metadata from an email, including company name, subject, and date."""
    subject = get_header(headers, 'Subject', 'No Subject')
    date = get_header(headers, 'Date', 'No Date')
    from_header = get_header(headers, 'From', None)
    company_name = extract_company_name(from_header, snippet)
    return company_name, subject, date

def extract_company_names(service, messages):
    """Extract company names and associated email metadata from a list of messages."""
    company_data = []
    for message in messages:
        try:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            snippet = msg['snippet']

            company_name, subject, date = extract_email_metadata(headers, snippet)

            if company_name:
                company_data.append((company_name, subject, date))
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            continue

    return list(set(company_data))

def clean_date(date_str):
    """Clean and parse the date string, removing timezone information and reformatting the date."""
    try:
        cleaned_date = date_str.split(' (')[0]
        parsed_date = datetime.strptime(cleaned_date, '%a, %d %b %Y %H:%M:%S %z')
        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        logging.error(f"Error parsing date: {date_str} -> {e}")
        return None

def save_to_csv(company_data):
    """Save the list of companies and related data to a CSV file, sorted by date (most recent first)."""
    try:
        sorted_data = sorted(
            [data for data in company_data if clean_date(data[2])],
            key=lambda x: clean_date(x[2]), 
            reverse=True
        )

        with open(OUTPUT_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Company Name", "Email Subject", "Date"])
            for data in sorted_data:
                writer.writerow([data[0], data[1], clean_date(data[2])])

        logging.info(f"Data successfully saved to {OUTPUT_FILE}.")
        print(f"Companies applied to (most recent first):")
        for data in sorted_data:
            print(f"Company: {data[0]}, Subject: {data[1]}, Date: {clean_date(data[2])}")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")
        raise

def main():
    """Main function to authenticate, search for emails, and process the results."""
    try:
        service = authenticate_gmail()
        messages = search_emails(service)
        if not messages:
            logging.info('No job application emails found.')
        else:
            company_data = extract_company_names(service, messages)
            save_to_csv(company_data)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
