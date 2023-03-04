import pylink
import re
import time
import subprocess

from pynrfjprog import HighLevel


api = HighLevel.API()

class environmentConfig():
    def __init__(self):
        pass

    def get_probe_snrs(self, api):
        with HighLevel.API() as api:
            programmers = api.get_connected_probes()
        return programmers

class boardInfo():
    def __init__(self, name = None, targetCPU = 'NRF52832_XXAB') -> None:
        self.name = name
        self.target_device = targetCPU
        self.mac = None
        
    def jlink_connect(self, serialNum):
        #Establishes Jlink connection to test object
        jlink = pylink.JLink()
        jlink.open(serial_no=serialNum)
        jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        jlink.connect(self.target_device)
        jlink.rtt_start()
        print("Connect success!")
        return jlink

    def jlink_close(self, jlink):
        try:
            jlink.close()
            print("Close JLINK success")
        except:
            print("Close JLINK Failed")

    def readMac(self, serialNum = None):
        bitwiseconstant = 0xC0
        # print(f'programmer value: {programmers}')
        if serialNum:
            subprocess1 = subprocess.Popen(f"nrfjprog --memrd 0x100000A4 --n 8 --snr " + str(serialNum), shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            output, errors = subprocess1.communicate()
        else:
            subprocess1 = subprocess.Popen(f"nrfjprog --memrd 0x100000A4 --n 8", shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            output, errors = subprocess1.communicate()
        
        try:
        # print("reading from memory address: 0x10000A4")
            # print(errors)
            static_msb = int(output[25:27], 16)
            convertmsb = static_msb | bitwiseconstant
            msbhex = hex(convertmsb)
            adv_macA = msbhex[2:4] + output[27:29] + (output[12:20])
            print(f"Device mac: {adv_macA.upper()}")
            self.mac = adv_macA.upper()
            return adv_macA.upper()
        except:
            print(f"[ERROR]: failed to get MAC ID, please check segger connection, board voltage.")

    
    def flash_mcu(self, snr, FW):
        program_options = HighLevel.ProgramOptions(
            erase_action=HighLevel.EraseAction.ERASE_ALL,
            reset=HighLevel.ResetAction.RESET_SYSTEM,
            verify=HighLevel.VerifyAction.VERIFY_READ
        )

        program = str(FW)
        print("programming file at : " + program)
        #print(snr)
        with HighLevel.API() as api:
            with HighLevel.DebugProbe(api, snr[0]) as probe:
                result = probe.program(program, program_options=program_options)
                if result == None:
                    print("SUCCESS!")

                probe.verify(program)

    def program(self, fwname):
        serial = environmentConfig().get_probe_snrs(api)
        try:
            self.flash_mcu(serial, fwname)
            return True
        
        except Exception as e:
            print(f'[ERROR]: Failed to program: {e}')
            return False