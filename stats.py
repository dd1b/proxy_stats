#!/usr/bin/python3
from __future__ import print_function

import os
import os.path
import math
import pdb
import pathlib
import configparser

import pandas as pd
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

dir_path = str(pathlib.Path(__file__).parent.resolve())

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

config = configparser.ConfigParser()
config.read(dir_path+'/stats_config.ini')

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = config["DEFAULT"]["SAMPLE_SPREADSHEET_ID"]


def test():
    """Shows basic usage of the Sheets API.
    Print values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(dir_path+'/token.json'):
        creds = Credentials.from_authorized_user_file(dir_path+'/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                dir_path+ '/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(dir_path+'/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        print('Name, Major:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('%s, %s' % (row[0], row[4]))
    except HttpError as err:
        print(err)


def init_connection_to_google_sheet():
    """Read token.json and
    create connection to google sheet
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(dir_path+'/token.json'):
        creds = Credentials.from_authorized_user_file(dir_path+'/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                dir_path+ '/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(dir_path+'/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)
        return service

    except HttpError as err:
        print(err)


def export_data_to_sheet(service, df):
    """
    Write data from pandas object to Google Sheet
    :param service: connection to google sheet
    :param df: pandas object with data to be written in google sheet
    """
    global ex
    df = df.fillna(0)
    df = df.rename_axis('Date').reset_index()
    data = [df.columns.values.tolist()]
    data.extend(df.values.tolist())

    _value_range_body = {
        "majorDimension": "COLUMNS",
        "values":
            data
    }
    _value_range_body = {"values": data}

    # determine range of google sheet
    _no_of_columns = len(data[0])
    _segments = math.floor(_no_of_columns / 26)
    range_name = "B1:EZ1000"
    if _segments > 1:
        if _segments < 26 * 25:  # there are 195 contries worldwide...but still....
            _first_letter = (chr(ord('a') + (_segments - 1))).upper()
            _second_letter_position = math.ceil(
                (_no_of_columns / 26 - _segments) * 26) + 1  # +1 because we will write starting with B column
            _second_letter = (chr(ord('a') + _second_letter_position)).upper()
            range_name = "B1:{}{}{}".format(_first_letter, _second_letter, len(data))
        else:
            print("Something bad happened...too many CC generated in raw data")
            return 0
    print(range_name)

    try:
        response_date = service.spreadsheets().values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            valueInputOption='RAW',
            range=range_name,
            body=_value_range_body
        ).execute()
        print('Sheet successfully Updated')
    except BaseException as ex:
        print(ex)


def get_data_from_files(dir_name):
    """
    Read data from folder and store in dict object
    :param dir_name: name of folder with raw data
    :return: dict object DATE -> CC -> TwoLetterCountryCode: NoOfAppearances
                              -> SOCKET -> IP:PORT : NoOfAppearances
    """
    my_dict = {}
    for root, dirs, files in os.walk(dir_name):
        if len(dirs) == 0:
            _day = root.split("/")[-1]
            my_dict[_day] = {}
            my_dict[_day]["CC"] = {}
            my_dict[_day]["SOCKET"] = {}
            for proxy_list in files:
                with open(os.path.join(root, proxy_list)) as f:
                    lines = f.readlines()
                    for line in lines:
                        _aux = line.split(",")
                        _ip = _aux[0]
                        _port = _aux[1]
                        _cc = _aux[2] if len(_aux[2]) == 2 else _aux[-1].strip()
                        # if country in dict increment, else initialize with 1
                        if _cc in my_dict[_day]["CC"].keys():
                            my_dict[_day]["CC"][_cc] = my_dict[_day]["CC"][_cc] + 1
                        else:
                            my_dict[_day]["CC"][_cc] = 1

                        # if IP:PORT in dict increment, else initialize with 1
                        _socket = "{}:{}".format(_ip, _port)
                        if _socket in my_dict[_day]["SOCKET"].keys():
                            my_dict[_day]["SOCKET"][_socket] = my_dict[_day]["SOCKET"][_socket] + 1
                        else:
                            my_dict[_day]["SOCKET"][_socket] = 1
    return my_dict


def put_data_in_good_format(var_myDict):
    """
    Read data from dict object and return one pandas object
    :param _myDict: dictionary with data about number of proxy by country code and number of sockets
            with key being a string with the day of the year YYYMMDD
    """
    df = pd.DataFrame()
    print("No. of days: {}".format(len(var_myDict.keys())))
    for _date in var_myDict.keys():
        _aux_df = pd.DataFrame([var_myDict[_date]["CC"]], index=[_date])
        df = pd.concat([df, _aux_df])
    print(df)
    return df


if __name__ == '__main__':
    _service = init_connection_to_google_sheet()

    _raw_data = get_data_from_files('dir_proxies')
    _df = put_data_in_good_format(_raw_data)

    export_data_to_sheet(_service, _df)

