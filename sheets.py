from __future__ import print_function
from dotenv import load_dotenv
import os.path

from google.oauth2 import service_account
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
assert SPREADSHEET_ID is not None
URL_RANGE = 'Tracker!A2:A'
USER_RANGE = 'Tracker!H1:1'


def write_to_spreadsheet(spreadsheet_id: str, range: str, values = list[list[any]]):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    #Use service account instead
    if os.path.exists('service.json'):
        creds = service_account.Credentials.from_service_account_file(
                'service.json', scopes=SCOPES)    
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not (creds.valid or isinstance(creds, service_account.Credentials)):
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
        body = {
            'values': values
        }

        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range,
            valueInputOption="USER_ENTERED", body=body).execute()

        print(f"{result.get('updatedCells')} cells updated.")
        return result

    except HttpError as err:
        print(err)


def read_from_spreadsheet(spreadsheet_id: str, range: str):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('service.json'):
        #Use service account instead
        creds = service_account.Credentials.from_service_account_file(
                'service.json', scopes=SCOPES)
        # assert isinstance(creds, Credentials)
        
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not (creds.valid or isinstance(creds, service_account.Credentials)):
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
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return []

        return values
    except HttpError as err:
        print(err)

def generate_url_to_index():
    raw_values = read_from_spreadsheet(SPREADSHEET_ID, URL_RANGE)
    if not raw_values:
        print('No URL data found.')
        return {}

    # TODO: Make this a named tuple if more metadata is necessary
    return {data[0]: index + 2 for index, data in enumerate(raw_values)}

async def add_new_doujin(url_to_index, url, title, circle_name, author_name, genre, is_r18, price_in_yen, price_in_usd):
     # Call the Sheets API
    values = [
        [
            url, title, f"{circle_name} ({author_name})", genre, is_r18, price_in_yen, price_in_usd
        ],
    ]

    index_of_new_doujin = len(url_to_index) + 2
    range_for_new_doujin = f"A{index_of_new_doujin}:G{index_of_new_doujin}"
    write_to_spreadsheet(SPREADSHEET_ID, range_for_new_doujin, values)
    url_to_index[url] = index_of_new_doujin

def generate_user_to_index():
    raw_values = read_from_spreadsheet(SPREADSHEET_ID, USER_RANGE)
    if not raw_values:
        print('No User data found.')
        return {}

    # TODO: Fix this so more people can hop on
    return {data[0]: chr(ord("H") + index) for index, data in enumerate(raw_values)}


async def add_user_to_spreadsheet(username_to_index: dict, username: str):
    values = [
                [
                    username
                ],
            ]
    column_for_new_username = chr(ord("H") + len(username_to_index))
    range_for_new_username = f"{column_for_new_username}1"

    write_to_spreadsheet(SPREADSHEET_ID, range_for_new_username, values)
    username_to_index[username] = column_for_new_username

def add_user_to_doujin(username_to_index: dict, url_to_index: dict, username: str, url: str):
    values = [
        [
            "X"
        ],
    ]
    range_to_add = f"{username_to_index[username]}{url_to_index[url]}"
    write_to_spreadsheet(SPREADSHEET_ID, range_to_add, values)

def remove_user_from_doujin(username_to_index: dict, url_to_index: dict, username: str, url: str):
    values = [
        [
            ""
        ],
    ]

    range_to_remove = f"{username_to_index[username]}{url_to_index[url]}"
    write_to_spreadsheet(SPREADSHEET_ID, range_to_remove, values)

if __name__ == '__main__':
    url_to_index = generate_url_to_index()
    print(url_to_index)

    user_to_index = generate_user_to_index()
    print(user_to_index)
