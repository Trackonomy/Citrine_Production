import requests
import json
import datetime


class sandbox_tool():
    def __init__(self, QR=None, mac=None) -> None:
        self.qr = QR
        self.mac = mac
    
    def add(self) -> bool:
        try:
            API_ENPOINT = "multitenantprod.azure-api.net"
            url = "https://multitenantprod.azure-api.net/config/internal/get_config?qrcode="+str(self.qr)
            url2 = "https://multitenantprod.azure-api.net/config/internal/add_row?qrcode="+str(self.qr)+"&tape_id="+str(self.mac)
            payload={}
            headers = {
                'customer_id': 'TRACKONOMY',
                'authorized_groups': 'SB'
                }
            #we have to check if the config exists, because add_row is allowing for duplicate configs
            response = requests.request("get",url,headers=headers,data=payload)
            if response.text:
                if str(json.loads(response.text)[0]['qrcode'] == self.qr):
                    print("[INFO]: Config exists but with same QR")
                    return True
                else:
                    print("Config EXISTS skipping add_row")
                    return False
            else:
                print("CONFIG Does not exist. Adding row into tape_config")
                response = requests.request("get",url2,headers=headers, data = payload)
                return True
        except KeyError as e:
            print(e)
            return False
    
    def delete(self) -> None:
        url3 = "https://multitenantprod.azure-api.net/config/internal/delete_row?qrcode="+str(self.qr)
    
        payload={}
        headers = {
            'customer_id': 'TRACKONOMY',
            'authorized_groups': 'SB'
            }
        #try:
        response = requests.request("get",url3,headers=headers,data=payload)
        if response.status_code == 200:
            #text = json.loads(response.text)
            print('response = ',response.text)

        #except:
        #    pass

    def checkHistory(self, parameter, start_time):
        '''
        Will only check the latest transmission
        '''
        try:
            url = "https://multitenantprod.azure-api.net/dash/get_history?qrcode=" + str(self.qr) + ("&override=True")
            payload = {}
            headers = {
                'customer_id': 'TRACKONOMY',
                'authorized_groups': 'SB'
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            test_data = json.loads(response.text)
            Strippedstring = test_data[0]['ts'][:-5]
            transmission_time= Strippedstring.replace('T',' ')
            transmission_time = datetime.datetime.strptime(transmission_time, '%Y-%m-%d %H:%M:%S')
            elapsed_time =(start_time - transmission_time)
            if elapsed_time < datetime.timedelta(minutes=5):
                try:
                    return test_data[parameter]
                except:
                    return "parameter does not exist"
            else:
                return "No broadcast"
        except:
            return "issue with api call"