from __future__ import print_function
from dotenv import load_dotenv
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
URL_RANGE = 'Tracker!A2:A'
USER_RANGE = 'Tracker!H1:1'


def generate_url_to_index():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=URL_RANGE).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        # TODO: Make this a named tuple if more metadata is necessary
        return {data[0]: index + 2 for index, data in enumerate(values)}
    except HttpError as err:
        print(err)

async def add_new_doujin(url_to_index, url, title, circle_name, author_name, genre, is_r18, price_in_yen):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        values = [
            [
                url, title, f"{circle_name} ({author_name})", genre, is_r18, price_in_yen
            ],
        ]
        body = {
            'values': values
        }

        index_of_new_doujin = len(url_to_index) + 1
        range_for_new_doujin = f"A{index_of_new_doujin + 1}:F{index_of_new_doujin + 1}"
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_for_new_doujin,
            valueInputOption="USER_ENTERED", body=body).execute()

        print(f"{result.get('updatedCells')} cells updated.")
        url_to_index[url] = index_of_new_doujin

    except HttpError as err:
        print(err)

def generate_user_to_index():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=USER_RANGE).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return {}
        # TODO: Fix this so more people can hop on
        return {data[0]: chr(ord("H") + index) for index, data in enumerate(values)}
    except HttpError as err:
        print(err)

async def add_user_to_doujin(username_to_index: dict, url_to_index: dict, username: str, url: str):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # TODO: Fix this so more people can hop on
        service = build('sheets', 'v4', credentials=creds)
        if username not in username_to_index:
            values = [
                [
                    username
                ],
            ]
            body = {
                'values': values
            }

            column_for_new_username = chr(ord("H") + len(username_to_index))
            range_for_new_username = f"{column_for_new_username}1"
            result = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, range=range_for_new_username,
                valueInputOption="USER_ENTERED", body=body).execute()

            print(f"{result.get('updatedCells')} cells updated.")
            url_to_index[username] = username

        values = [
            [
                "X"
            ],
        ]
        body = {
            'values': values
        }

        range_to_add = f"{username_to_index[username]}{url_to_index[url]}"
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_to_add,
            valueInputOption="USER_ENTERED", body=body).execute()

        print(f"{result.get('updatedCells')} cells updated.")

    except HttpError as err:
        print(err)

if __name__ == '__main__':
    url_to_index = generate_url_to_index()
    print(url_to_index)

    user_to_index = generate_user_to_index()
    print(user_to_index)
