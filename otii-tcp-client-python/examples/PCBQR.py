
#!/usr/bin/env python
import time
import sys, os
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from otii_tcp_client import otii_connection, otii_exception, otii
import example_config as cfg
import subprocess

def check_create_project(otii_object):
    proj = otii_object.get_active_project()
    if proj:
        print("Project already active")
    else:
        proj = otii_object.create_project()
        print("Project created")
    return proj


def enable_channels(otii_object, my_arc):
    print(my_arc.name + " supply voltage = " + str(my_arc.get_main_voltage()))
    my_arc.enable_channel("mc",True)
    otii_object.set_all_main(True)
    print("POWER ON")

if __name__ == '__main__':
    connection = otii_connection.OtiiConnection(cfg.HOST["IP"],cfg.HOST["PORT"])
    connect_response = connection.connect_to_server()
    if connect_response["type"] == "error":
        print("Exit! Error code: " + connect_response["errorcode"] + ", Description: " + connect_response["data"]["message"])
        sys.exit()
    otii_object = otii.Otii(connection)
    devices = otii_object.get_devices()
    #print(devices)
    if len(devices) == 0:
        print("No Arc connected!")
        sys.exit()
    my_arc = devices[0]
    proj = check_create_project(otii_object)
    enable_channels(otii_object,my_arc)
    proj.start_recording()

   # subprocess1 = subprocess.Popen(r"JLinkRTTLogger.exe -Device NRF52810_XXAA -if SWD -Speed 4000Khz -RTTChannel 0 C:\Users\garre\Trackonomy\Desktop\New_folder\tests.txt", shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

   # output, errors = subprocess1.communicate()

    #print(output)


