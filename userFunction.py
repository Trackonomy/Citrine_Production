import json
import requests
from requests.models import PreparedRequest
import time

API_ENDPOINT = "http://vmprdate.eastus.cloudapp.azure.com:9000/api/v1/manifest"

def checkQR(QR):
    '''
    Check if QR exists in the database
    return: 
        True -> not exist
        False -> exist
    '''
    params = {"qrcode": QR}
    req = PreparedRequest()
    req.prepare_url(API_ENDPOINT, params)
    payload = {}
    headers = {}

    try:
        response = requests.request("GET", req.url, headers=headers, data=payload, timeout=20)
    except:
        print('response for check QR code failed')

    res_dict = json.loads(response.text)

    # A success response
    if response.status_code == 200:
        # when QR does not Exist, return True
        if  res_dict['error']:
            return True
        # when QR is not exist
        else:
            print(f"[ERROR]: QR Code {QR} exists in the DB!")
            return False
    # when server error
    else:
        print(f'[ERROR]: server respond other than 200')
        return False

def getQR():
    '''
    return: user input QR
    '''
    qrCode = input("Please scan QR:\n")
    return qrCode

    
def getBrdQR():
    '''
    return: user input board QR
    '''
    qrCode = input("Please scan board QR:\n")
    return qrCode


def checkMac(mac):
    '''
    Check if mac exists in the database
    return: 
        True -> not exist
        False -> exist
    '''
    params = {"macid": mac}
    req = PreparedRequest()
    req.prepare_url(API_ENDPOINT, params)
    payload = {}
    headers = {}

    try:
        response = requests.request("GET", req.url, headers=headers, data=payload, timeout=20)
    except:
        print('response for check mac code failed')

    res_dict = json.loads(response.text)

    # A success response
    if response.status_code == 200:
        # when mac Exist
        if res_dict['error']:
            return True

        # when mac is not exist
        else:
            print(f"[ERROR]: mac {mac} exists in the DB!")
            return False
    # when server error
    else:
        print(f'[ERROR]: server respond other than 200')
        return False