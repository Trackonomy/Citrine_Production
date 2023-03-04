import json
import requests
from requests.models import PreparedRequest
import time
import datetime

API_ENDPOINT = "http://vmprdate.eastus.cloudapp.azure.com:9000/api/v1/manifest"


class databaseInfo():
    def __init__(self, QR=None, mac=None):
        self.QR = QR
        self.mac = mac
        self.dbRecord = None

    def getInfo_QR(self):
        """
        Get db info by using QR
        return False if already exist
        """
        params = {"qrcode": self.QR}
        req = PreparedRequest()
        req.prepare_url(API_ENDPOINT, params)
        payload = {}
        headers = {}

        try:
            response = requests.request("GET", req.url, headers=headers, data=payload, timeout=20)
        except:
            print('response for check QR code failed')

        res_dict = json.loads(response.text)
        self.dbRecord = res_dict

        # A success response
        if response.status_code == 200:
            # when QR Exist
            if not res_dict['error']:
                self.mac = res_dict['data'][0]['macid']
                return res_dict

            # when QR is not exist
            else:
                print(f"[INFO] QR Code {self.QR} does not exists in the DB!")
                return False
        # when server error
        else:
            print(f'[ERROR]: server respond other than 200')
            return False
    
    def getInfo_mac(self):
        """
        Get db info by using mac
        return False if it already exists
        """
        params = {"macid": self.mac}
        req = PreparedRequest()
        req.prepare_url(API_ENDPOINT, params)
        payload = {}
        headers = {}

        try:
            response = requests.request("GET", req.url, headers=headers, data=payload, timeout=20)
        except:
            print('response for check mac code failed')

        res_dict = json.loads(response.text)
        self.dbRecord = res_dict

        # A success response
        if response.status_code == 200:
            # when QR Exist
            if not res_dict['error']:
                self.QR = res_dict['data'][0]['qrcode']
                print(f"[INFO] {self.mac} exists in the DB!")
                return res_dict

            # when QR is not exist
            else:
                print(f"[INFO] mac {self.mac} does not exists in the DB!")
                return False
        # when server error
        else:
            print(f'[ERROR]: server respond other than 200')
            return False

    # Unncessary function, to get Mac/QR only, now can be get by access its instance.
    # def getDBMac(self):
    #     """
    #     Get mac based on QR
    #     """
    #     oldData = self.getInfo_QR()
    #     try:
    #         self.mac = oldData['data'][0]['macid']
    #         return True
    #     except:
    #         self.mac = "Invalid QR, QR does not exist"
    #         return False

    # def getDBQR(self):
    #     """
    #     Get QR based on mac
    #     """
    #     oldData = self.getInfo_mac()
    #     try:
    #         self.QR = oldData['data'][0]['qrcode']
    #         return True
    #     except:
    #         self.QR= "Invalid mac, mac does not exist"
    #         return False

    def returnMac(self):
        print(f"Database mac: {self.mac}")
        return self.mac.upper()

    def update_Info(self, tapeType, hwType, hwVersion, fwVersion, customerFWVersion):
        '''
        params is a dict, with following format:
        {"Field": Value, etc}
        '''
        DBdata = self.getInfo_QR()
        
        oldComment = DBdata['data'][0]['comment']
        
        req = requests.PreparedRequest()
        headers = {}
        version = hwType + hwVersion + 'fw' + fwVersion
        SWrevision = tapeType + '-' + version + '-' + 'FW' + customerFWVersion

        columns = {'qrcode': self.QR, 'SWrevision': SWrevision, 'fw_version': str(SWrevision)}
        columns['comment'] = str(oldComment) + '| ' + str(version) + ' @ ' + str(time.strftime("%Y-%m-%d %H:%M"))

        try:
            r = requests.request("PUT", API_ENDPOINT, headers=headers, json=columns, timeout=10)
            # update db record
            self.getInfo_QR()
            print(f'Update device {self.QR} complete')
            return True
        except:
            print(f'[Error]: Update device {self.QR} failed')
            return False
        
    def add_Info(self, SIMID="000000000000000000000", SIMTYPE = None, batType = "320 mAh", batQty = 1, firmwareParam = "Onyx 1.2", pcbaParam = "Onyx1.2", targetState = None, comment = None, tapeColor = None):
        SIMTYPE = "iBasis Global" + "|" + str(self.QR)
        SIMID1 = SIMID[0:17]
        SIMID2 = SIMID[17:]
        comment = SIMTYPE

        now = datetime.datetime.now()
        now = now.strftime('%m/%d/%Y %H:%M:%S')

        print("updating info")
        '''DATA TO BE SENT (FORMAT: {"COLUMN_NAME1": VALUE1, "COLUMN_NAME2": VALUE2.....})'''
        columns = {"qrcode": self.QR, "macid": self.mac, "SWrevision": firmwareParam, "AssyDate": now, "batteryType": batType,
                "serialized": "Yes", "tapeColor": tapeColor, "fw_version": firmwareParam, "SWrevision": firmwareParam,
                "PCBA": pcbaParam, "hw_version": pcbaParam, "SIMcard": SIMID1, "SIMcard1": SIMID2, "SIMactive":"Yes",
                "targetState": targetState,
                "batteryQty": batQty, "comment": comment, "VThreshold": 2.9}

        headers = {}

        response = requests.request("PUT", API_ENDPOINT, headers=headers, data=columns, timeout=10)
        return 'UPDATE {}. '.format(self.QR) + response.text