from __future__ import print_function
from dotenv import load_dotenv
import os.path

from typing import Dict, List, Any, Tuple
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from scrape import Doujin
load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
assert SPREADSHEET_ID is not None
URL_RANGE = 'Tracker!A2:A'
USER_RANGE = 'Tracker!1:1'


def write_to_spreadsheet(spreadsheet_id: str, range: str, values: List[List[Any]]):
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

#returns a list of doujins that the user has subscribed to.
async def get_user_doujins(url_to_index, user_to_index, user: str) -> List[Dict[str, Any]]:
    if user not in user_to_index:
        return []
    
    index_of_doujins = len(url_to_index) + 1

    range_for_user = f"{user_to_index[user]}{2}:{user_to_index[user]}{index_of_doujins}"
    flip = dict((v - 2,k) for k,v in url_to_index.items())
    values = read_from_spreadsheet(SPREADSHEET_ID, range_for_user)
    assert isinstance (values, list)
    return [{'id' : ind, 'data' : (flip[ind], *v)} for ind, v in enumerate(values) if len(v) == 1]
    
def generate_user_to_index():
    raw_values = read_from_spreadsheet(SPREADSHEET_ID, USER_RANGE)
    if not raw_values:
        print('No User data found.')
        return {}

    # TODO: Fix this so more people can hop on
    return {data: chr(ord("H") + index) for index, data in enumerate(raw_values[0][7:])}


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

def does_user_have_doujin(username_to_index: dict, url_to_index: dict, username: str, url: str) -> bool:
    range_to_check = f"{username_to_index[username]}{url_to_index[url]}"
    values = read_from_spreadsheet(SPREADSHEET_ID, range_to_check)
    if values is None:
        raise ValueError
    if values == []:
        return False
    
    return values[0][0] == 'X'

def who_has_doujin(username_to_index: dict, url_to_index: dict, url: str) -> List[str]:
    range_to_check = f"{'Tracker!H'}{url_to_index[url]}:{chr (ord('H') + len(username_to_index))}{url_to_index[url]}"
    print (range_to_check)
    values = read_from_spreadsheet(SPREADSHEET_ID, range_to_check)
    if values is None:
        raise ValueError
    
    if values == []:
        return []
    
    values = values[0]
    # pad to make same size
    values.extend ([''] * (len(username_to_index) - len(values)))
        
    print (values, username_to_index)
    return [key for key, value in username_to_index.items() if values[ord (value) - 72] == 'X']

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

def frontload_doujins_fromdb(url_to_index: dict) -> Dict[str, List[str]]:
    values = read_from_spreadsheet(SPREADSHEET_ID, f'DB!A1:I{len(url_to_index) + 1}')
    assert isinstance (values, List)
    
    return {x[0]:x for x in values}

def add_to_db(doujin_to_add: Doujin, url: str, url_to_index: Dict[str, int], prev: Dict[str, List[str]]):
    title, price_in_yen, circle_name, author_name, \
                genre, event, is_r18, image_preview_url = doujin_to_add
    values = [[
                url, title, circle_name, author_name, genre, is_r18, price_in_yen, event, image_preview_url
            ]]
    index_of_new_doujin = len(url_to_index) + 1

    write_to_spreadsheet(SPREADSHEET_ID, f'DB!A{index_of_new_doujin}:I{index_of_new_doujin}',values)
    prev[url] = values[0]


if __name__ == '__main__':
    url_to_index = generate_url_to_index()
    print(url_to_index)

    user_to_index = generate_user_to_index()
    print(user_to_index)
    
    def back_port_doujins (url_to_index: Dict[str, int]):
        from scrape import scrape_url
        
        values = []
        for url in url_to_index:
            title, price_in_yen, circle_name, author_name, \
                genre, event, is_r18, image_preview_url = scrape_url(url)
                
            values.append (
                [
                    url, title, circle_name, author_name, genre, is_r18, price_in_yen, event, image_preview_url
                ]
            )
            
        write_to_spreadsheet(SPREADSHEET_ID, f'DB!A1:I{len(values) + 1}',values)
        
    back_port_doujins(url_to_index)
