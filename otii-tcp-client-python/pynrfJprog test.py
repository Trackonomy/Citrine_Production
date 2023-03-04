from os import path
from pynrfjprog import HighLevel
from pynrfjprog.APIError import *
import questionary
import os.path
from requests.models import PreparedRequest
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import subprocess
from datetime import datetime, timedelta
import logging
import requests
import json
import time
import sys, os
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
#from example_get_channel_data_and_count import get_channel_data, get_channel_data_count
from otii_tcp_client import otii_connection, otii_exception, otii
#from example_get_channel_data_and_count import *
import example_config as cfg

SPREADSHEET_ID = ''
SPREADSHEET_RANGE = ''
logging.basicConfig(level=logging.INFO)
creds = None
api = HighLevel.API()

API_ENDPOINT = "http://vmprdate.eastus.cloudapp.azure.com:9000/api/v1/manifest"

global start_time
# http://45.33.42.32:6214/add_row?qrcode=1C-181021-00-E0C890&tape_id=DE1DAAC29165
#http://45.33.42.32:6214/edit_config?qrcode=1C-181021-00-E0C890&timeoutPeriod=1800&rssi_threshold=-110&nlps=0&lcd=20&bcd=10&bad=20&bsfid=5258&bafid=5258&pgtl=1000&pgtt=1800000&at=20&atd=4&gsd=1
#http://45.33.42.32:6022/get_history?qrcode=1C-181021-00-E0C890
'''
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
'''

####   OTII FUNCTIONS #####


def check_create_project(otii_object):
    proj = otii_object.get_active_project()
    if proj:
        print("Project already active")
    else:
        proj = otii_object.create_project()
        print("Project created")
    return proj


def enable_channels(otii_object,proj, my_arc):
    print(my_arc.name + " supply voltage = " + str(my_arc.get_main_voltage()))
    my_arc.enable_channel("mc",True)
    otii_object.set_all_main(True)
    print("POWER ON")
    proj.start_recording()

def get_channel_data_count(recording, device_id, channel):
    samples = recording.get_channel_data_count(device_id, channel)
    print("No. samples: " + str(samples))
    return samples

def get_channel_data(recording, device_id, channel, index, count):
    data = recording.get_channel_data(device_id, channel, index, count)
    print("No. samples: " + str(len(data["values"])))
    if len(data) > 0:
        print("First data item of " + str(len(data["values"])) + " is: " + str(data["timestamp"]) + " s, " + str(data["values"][0]) + " A")

    print(sum(data["values"]))
    print(len(data['values']))
    print(type(len(data)))
    avgvalue = sum(data['values']) / len(data['values'])
    print("average current : ",avgvalue)
    return(avgvalue)

def reset_otii(otii_object):
    otii_object.set_all_main(False)
    time.sleep(2)
    otii_object.set_all_main(True)
    time.sleep(2)

def ProgramUpdate(api,otii_object):
    MO = False
    MU = False
    Modem_FW = False
    MCU_FW = False

    ## Get Serial Numbers of Debuggers
    serial = get_probe_snrs(api)
    if len(serial) == 2: 
        print(serial[0],"MCU and " , serial[1], "Modem Ready to program!")

    else:
        print("Can't detect 1 or more programmers.\n")
        return False
    
      
    
    try:
        print("Flashing Modem power firmware\n")
        flash_mcu(serial[0],"\Modem_Power_ON_Firmware.hex",path)
        MO = True
        reset_otii(otii_object)
    except:
        print("failed to program MCU, please check power and programmer connections\n")
        

    if MO:
        print("\n UPDATING MODEM this may take up to 1 minute")

        try:
            Update_modem(serial[1])
            MU = True
            
        except:
            print("Failed to update modem\n")

    if MU:

        
    
        try:
            flash_mcu(serial[1],r"\nrf9160_Firmware.hex",path)
            Modem_FW = True
        except:
            print("Failed to Program Modem\n")

    if Modem_FW:

    
        try:
            flash_mcu(serial[0],r"\IGPS_merged.hex",path)
            MCU_FW = True
            
            
        
        except:
            print("Failed Final Programming step")
    #print(MO,MU,Modem_FW,MCU_FW)
    if  False in (MO, MU, Modem_FW, MCU_FW):
        print("Failed to pass programming stage")
        return False
        exitprogram()

    if MO and MU and Modem_FW and MCU_FW:
        print("successfully completed programming")
        return True




def getBoardInfo():
    #boardNumber = questionary.text("Please enter board number.").ask() #####Do we need this???#####

    select = False
    while (select == False):
        QR = questionary.text("Please Scan QR code.").ask()
        SIM = questionary.text("Please enter SIM number.").ask()
        print ("QR = "+QR + " and SIM = " +SIM)
        confirmed = questionary.select("Is this board info correct?", choices=["Yes\n", "No\n"]).ask()
        if confirmed == "Yes\n":
            select = True
        if confirmed == "No\n":
            print("OK, please rescan the information")
            print("\n" *2)
            select = False
    
    return(QR, SIM)

def confirmBoard():
    if confirmed == "Yes":

        params = {'qrcode': QR}
        api_call("add_row",{"qrcode"})

    else:
        print()
        
        #getBoardInfo()

def activateModem():
    confirm = questionary.text("Please ensure that board is properly mounted on fixture \n \n When ready press Enter").ask()

    flash_mcu()



def api_call(setting, payload):
    ##this is only GPBP##

    r = requests.get("http://45.33.42.32:6214/" + setting , params = payload)
    print(r)
    return(r)





def get_probe_snrs(api):
    with HighLevel.API() as api:
        programmers = api.get_connected_probes() 
        return(programmers)




def flash_mcu(snr, FW,path):
    program_options = HighLevel.ProgramOptions(
                erase_action=HighLevel.EraseAction.ERASE_ALL,
                reset = HighLevel.ResetAction.RESET_SYSTEM,
                verify = HighLevel.VerifyAction.VERIFY_READ
            )
    
    program = (str(path + FW))
    print("programming file at : " + program)

    with HighLevel.API() as api:
    
    
        with HighLevel.DebugProbe(api,snr) as probe:
            
            result = probe.program(program,program_options = program_options)
            if result == None:
                print("SUCCESS!")
            
            probe.verify(program)



def get_mac(programmers):
    bitwiseconstant = 0xC0
    #with HighLevel.API() as api:
        
    print(programmers)
    subprocess1 = subprocess.Popen(f"nrfjprog --memrd 0x100000A4 --n 8 --snr " + str(programmers[0]), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output, errors = subprocess1.communicate()
    try:
        print("reading from memory address: 0x10000A4")
        #print(output)
        static_msb = int(output[25:27], 16)
        #print(static_msb)
        static_mac_id = (output[25:29]) + (output[12:20])
        hex2dec = int(static_mac_id, base=16)
        
        dec2bin = bin(hex2dec)
        
        convertmsb = static_msb | bitwiseconstant
        msbhex = hex(convertmsb)

        adv_macA = msbhex[2:4] + output[27:29] + (output[12:20])
        print(adv_macA.upper())
        print(type(adv_macA))
        return adv_macA.upper()
    
    except:
        print("failed to get MAC ID")





def Update_modem(snr):
    api = HighLevel.API()
    api.open()
    probe = HighLevel.IPCDFUProbe(api, snr, HighLevel.CoProcessor.CP_MODEM)
    probe.program("mfw_nrf9160_1.3.1.zip")
    probe.verify("mfw_nrf9160_1.3.1.zip")
    print("Modem Sucsessfully updated")
    api.close()

def api_call(setting, payload):
    ##this is only GPBP##

    r = requests.get("http://45.33.42.32:8172/" + setting , params = payload)
    print(r)
    return(r)

def endpoint_calls(QR,mac):

    r = api_call("add_row", {'qrcode':str(QR) , 'tape_id': str(mac)})
    if r.text == "OK":
            print("Added QR-MAC to endpoint")  
    else:
            print(r.text)
            #return False

    #r = api_call("edit_config",{'qrcode':'05-121121-01-H0C881&timeoutPeriod=1800&rssi_threshold=-110&nlps=0&lcd=20&bcd=10&bad=20&bsfid=5258&bafid=5258&pgtl=1000&pgtt=1800000&at=20&atd=4&gsd=1'})
    r = requests.get("http://45.33.42.32:8172/edit_config?qrcode=" + str(QR) +"&timeoutPeriod=1800&rssi_threshold=-110&nlps=0&lcd=20&bcd=10&bad=20&bsfid=5258&bafid=5258&pgtl=1000&pgtt=1800000&at=20&atd=4&gsd=1")
    #http://45.33.42.32:6214/edit_config?qrcode=05-121121-01-H0C881&timeoutPeriod=1800&rssi_threshold=-110&nlps=0&lcd=20&bcd=10&bad=20&bsfid=5258&bafid=5258&pgtl=1000&pgtt=1800000&at=20&atd=4&gsd=1

    ##HAVING ISSUE WITH THE API CALL USING THE REQUEST BUILDER FOR EDITCONFIG, WORKS FOR ADDROW THOUGH####

    #print(r)
    if r.text == "OK":
            print("Set Device Parameters")
            return True
    else:
            print(r.text)
            return False

def gethistory(QR):
    hum = False
    temp = False

    response = requests.get("http://45.33.42.32:8122/get_history?qrcode=" + str(QR))
    print(response)
    data = json.loads(response.text)
    values = data[0]
    print(data[0])
    try:
        for key, value in values.items():
        
            if (key == 't0'):
                param = value
                print(param)
                if int(value) >10 and int(value) < 50:
                    print("good reading of temp sensor")
                    temp = True
                
                else:
                    print("temp reading bad")
                    temp = False
            
            if (key =='h0'):
                param1 = value
                print(param1)
                if int(value) >10 and int(value) < 50:
                    print("good reading of humidity sensor")
                    hum = True
                else:
                    print("Hum reading bad")
                    hum = False

    except:    
        print('did not connect to server')
        return False

    if (temp == True and hum == True):
        print('connected to server and data sensors working properly')
        return (temp,hum)
    else:
        return False

        



def startlogger(programmers):
    print(r"JLinkRTTLogger.exe -Device NRF52832_XXAA -if SWD -Speed 4000Khz -SelectEmuBySN " + str(programmers[0]) + " -RTTChannel 0 C:\\Users\\garre\\Trackonomy\\Desktop\\Onyx_Test_programming\\tests.txt")
    subprocess1 = subprocess.Popen(r"JLinkRTTLogger.exe -Device NRF52832_XXAA -if SWD -Speed 4000Khz -SelectEmuBySN " + str(programmers[0]) + " -RTTChannel 0 C:\\Users\\garre\\Trackonomy\\Desktop\\Onyx_Test_programming\\tests.txt", shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    #subprocess1 = subprocess.Popen(r"JLinkRTTLogger.exe -Device NRF52810_XXAA -if SWD -Speed 4000Khz -SelectEmuBySN " + str(programmers[0]) + " -RTTChannel 0 C:\\Users\\garre\\Trackonomy\\Desktop\\Onyx_Test_programming\\tests.txt", shell = True, stdout=subprocess.PIPE,stderr = subprocess.PIPE,universal_newlines=TRUE)
    output, errors = subprocess1.communicate()

    print(output)


################################
###QR-MAC Database functions####
################################


def add2db(QR, mac, SIMID):
    SIMTYPE = "iBasis Global"
    columns1 = {"qrcode": QR}
    headers1 = {}
    response = requests.request("POST", url = API_ENDPOINT, headers = headers1, json= columns1, timeout = 10)
    res = response.text
    print(res)
    SIMID1 = SIMID[0:17]
    SIMID2 = SIMID[17:]
    comment = SIMTYPE
    WorkOrder = ""
    #return 'INSERT {}. '.format(QR) + res

    now = datetime.now()
    now = now.strftime('%m/%d/%Y %H:%M:%S')
    firmwareParam = "Onyx 1.2"
    pcbaParam = "Onyx 1.2"
    batQty = 1
    batType = "320 mAh"

    print("updating info")
    '''DATA TO BE SENT (FORMAT: {"COLUMN_NAME1": VALUE1, "COLUMN_NAME2": VALUE2.....})'''
    columns = {"qrcode": QR, "macid": mac, "SWrevision": firmwareParam, "AssyDate": now,"batteryType":batType
                ,"serialized": "Yes", "tapeColor": "Black","fw_version": firmwareParam, "SWrevision": firmwareParam , 
                "PCBA": pcbaParam, "hw_version": pcbaParam, "SIMcard": SIMID1,"SIMcard1":SIMID2, "targetState": "ONYXprogV1.0",
                "batteryQty": batQty, "comment":comment}


    

    headers = {}

    response = requests.request("PUT", API_ENDPOINT, headers=headers, data=columns, timeout=10)
    print(response.text)
    return 'UPDATE {}. '.format(QR) + response.text


def CheckQR(QR):
    """ Checks whether qrcode exists in db"""
    params = {"qrcode": QR  }
    req = PreparedRequest()
    req.prepare_url(API_ENDPOINT, params)

    payload = {}
    headers = {}

    try:
        response = requests.request("GET", req.url, headers=headers, data=payload, timeout=20)
    except:
        response = repeatedRetryCheck(req.url)

    if response.status_code == 200:
        res_dict = json.loads(response.text)
        if not res_dict['error']:
            data_dict = res_dict['data']
            raise Exception("ERROR : QR Code {} already exists in the DB!".format(QR))
            exitprogram()
        else:
            print('During CHECK - Server responded {}'.format(res_dict['message']))
            return 0
            #print("QR code does not yet exist")
    else:
        #print('Bad response from server. Status code = {}'.format(response.status_code))
        #return 0
        print("QR Check PASSED \n QR code does not yet exist")
    #print(data_dict)
    return 1

def Checkmac(mac):
    params = {"macid": mac}
    req = PreparedRequest()
    req.prepare_url(API_ENDPOINT, params)

    payload = {}
    headers = {}

    response = requests.request("GET", req.url, headers=headers, data=payload, timeout=10)
    if response.status_code == 200:
        res_dict = json.loads(response.text)
        if not res_dict['error']:
            data_dict = res_dict['data']
            raise Exception("ERROR : MAC ID {} already Exists in Database".format(mac))
        else:
            print('During CHECK - 200 Response from server but there is an error. {}'.format(res_dict['message']))
            return 0
    else:
        #print('Bad response from server. Status code = {}'.format(response.status_code))
        #return 0
        print("MAC check PASSED \n MAC ID does not yet exist")

    print(data_dict)
    return 1

def readfile(path):
    with open(path +"\\tests.txt" , 'r+') as file:
        if "HALL" in file.read():
            print("Hall effect test passed")
            file.truncate(0)
            return True
        else:
            print("Hall effect test: FAILED")
            file.truncate(0)
            return False
################################
###General purpose functions####

def createtestlog(QR,mac,Programming_passed,halltest, temptest,humtest,celltest):
        print('test')


def exitprogram( qrCheck = False, Programming_passed = False,halltest = False 
,endpoint_calls = False, temptest = False,humtest = False,sleeptest = False):
    
    global start_time



    testtime = datetime.now() - start_time
    print("" *3)
    print("TEST RESULTS")
    print("")
    print("Test Took " ,testtime)
    print("QR check : " ,qrCheck)
    print("Programming Passed : " ,Programming_passed)
    print("Endpoint Adds :", endpoint_calls)
    print("Hall effect test : ",halltest)
    print("Sensor tests : " , temptest)
    print("humidity sensor : ",humtest)
    print("Sleep test : ", sleeptest)
    #otii_object.set_all_main(False)
    sys.exit()




if __name__ == "__main__":

    global start_time
    start_time = datetime.now()
    path = r'Onyx_Test_programming'
    channel = "mc"
    index = 0

    qrCheck = False
    #tests: humidity,temp,cell service,sleep current,hall effect,programming
    ##################
    ####OTII Setup####
    """
    connection = otii_connection.OtiiConnection(cfg.HOST["IP"], cfg.HOST["PORT"])
    connect_response = connection.connect_to_server()
    if connect_response["type"] == "error":
        print("Exit! Error code: " + connect_response["errorcode"] + ", Description: " + connect_response["data"]["message"])
        sys.exit()
    
    
    otii_object = otii.Otii(connection)
    devices= otii_object.get_devices()
    my_arc = devices[0]
    """
    connection = otii_connection.OtiiConnection(cfg.HOST["IP"], cfg.HOST["PORT"])
    connect_response = connection.connect_to_server()
    if connect_response["type"] == "error":
        print("Exit! Error code: " + connect_response["errorcode"] + ", Description: " + connect_response["data"]["message"])
        exitprogram()
    try:
        otii_object = otii.Otii(connection)
        devices = otii_object.get_devices()
        if len(devices) == 0:
            print("No Arc connected!")
            exitprogram()
        my_arc = devices[0]
        proj = check_create_project(otii_object)
        
        enable_channels(otii_object,proj, my_arc)
    except otii_exception.Otii_Exception as e:
        print("Error message: " + e.message)

    
    ####################################
    ####Get Board information for DB####

    brdinfo = getBoardInfo()
    QR = brdinfo[0]
    SIMID = brdinfo[1]
    
    programmers = get_probe_snrs(api)
    
    mac = get_mac(programmers) ####with Demuxer we only need one programmer####
    if not mac:
        print("QUITTING")
        exitprogram()
    #add2db(QR,mac,SIMID)

    ###############################
    ###Check QR-MAC doesnt exist###
    ###############################
    
    qrCheck = CheckQR(QR)
    Checkmac(mac)
    

    ########################
    ###Program The device###
    Programming_passed = ProgramUpdate(api,otii_object)
    if Programming_passed == False:
        print("QUITTING")
        exitprogram()
    reset_otii(otii_object)
    
    ####
    ###Add device to endpoint###
    ###
    Endpoint_adds = endpoint_calls(QR,mac)
    
    
    #start hall effect testing###
    print("Testing Hall effect sensor Please swipe magnet over the PCB for the next 30 seconds.\n Press enter When ready to stop")
    startlogger(programmers)
    
    halltest = readfile(path)   
    if halltest == False:
        exitprogram()

    test_rdy = questionary.text("please remove the programmers and press enter AFTER the device has gone to sleep").ask() 
    print("checking server data")
    enable_channels(otii_object,proj,my_arc)
    sensor_data = gethistory(QR)
    temptest = sensor_data[0]
    humtest = sensor_data[1] 
    

    time.sleep(8)
    proj.stop_recording()
    #enable_channels(otii_object,proj,my_arc)
    #reset_otii(otii_object)
    
    
    recording = proj.get_last_recording()
    if recording:
            count = get_channel_data_count(recording, my_arc.id, channel)
            avg_current = get_channel_data(recording, my_arc.id, channel, index, count)
    else:
            print("No recording in project")

    qrCheck = True
    endpoint_calls = True
    print("Done!")
    
    if avg_current < .00002:
        i_sleep = True
        print("sleep test: PASSED")
        add2db(QR,mac,SIMID)
        otii_object.set_all_main(False)
        exitprogram(qrCheck,Programming_passed,halltest,endpoint_calls
        ,temptest,humtest,i_sleep)
    
    else:
        i_sleep = False
        otii_object.set_all_main(False)
        print("sleep test: FAILED")
        exitprogram()
        

    






















