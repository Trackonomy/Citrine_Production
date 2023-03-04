import databaseFunction
import hardwareFunction
import sequanceTool
import otiiControl
import testEnv

import concurrent.futures

from datetime import datetime

import os

import serial.tools.list_ports
import time

import sys


def programModem(COMPort):
    print(f"Update Modem appliction firmware via {COMPort}")
    COMClass = sequanceTool.sequance(COMPort)
    res = COMClass.program(currentPath, '.\\Cirtine-Binaries\\GM02RB6Q_LR8.0.5.11-56111.dup')
    return res




# Start of the script
startTime= datetime.now()

# Get board number
boardNum = int(input("Please enter the number of boards that needs be tested\n"))
# boardNum = 1
testList = ['qr', 'mac', 'Modem power on', 'modem firmware', 'test firmware', 'endpoint', 'battery', 'sleep current']

testRes_2D = [[False for _ in range(len(testList))] for _ in range(boardNum)]

# scan QR
qrCode = input("Please scan QR\n")
# qrCode = "123"
brdDatabase = databaseFunction.databaseInfo(qrCode)

# Check if QR exists
qrRes = brdDatabase.getInfo_QR()
if qrRes == False:
    testRes_2D[0][0] = True
else:
    print("Failed at QR check")
    sys.exit()

currentOtii = otiiControl.activeProj()

time.sleep(1)
# turn on Otii
for i in currentOtii.otiiList:
    i.set_main(True)

# get its mac
targetBrd = hardwareFunction.boardInfo()
macAddr = targetBrd.readMac()
brdDatabase.mac = macAddr

# Check if mac exists
macRes = brdDatabase.getInfo_mac()
if macRes == False:
    testRes_2D[0][1] = True
else:
    print("Failed at mac check")
    sys.exit()

currentPath = os.getcwd()

# program the board with modem power on firmware
programRes = targetBrd.program('.\\Cirtine-Binaries\\Citrine_V_1_2-Modem_ON.hex')

# Check if program modem power on success
if programRes:
    testRes_2D[0][2] = True
else:
    print("Failed at program Modem power on")
    sys.exit()
# get current address  

# Get list of COM port
# com_ports = serial.tools.list_ports.comports()
# for port, desc, hwid in sorted(com_ports):
#     print(f"{port}: {desc} [{hwid}]")


# program Modem application FW
COMList = ['COM9']
modemResultList = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(programModem, COMList[i]) for i in range(len(COMList))]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        modemResultList.append(future.result())

for i in modemResultList:
    if i :
        testRes_2D[0][3] = True
    else:
        print("Failed at program Modem firmware")
        sys.exit()

# program test firmware
programRes = targetBrd.program('.\\Cirtine-Binaries\\Citrine_V_1_2_Test.hex')

if programRes:
    testRes_2D[0][4] = True
else:
    print("Failed at program testing firmware")
    sys.exit()
# get debug info
# outputErr = p.stderr
# print(p.stderr)

# measure sleep current


# update comment
# updateRes = brdDatabase.update_Info("black", "on", "140", "100_testingfw", "1_0_0")


# add row
sandboxEntry = testEnv.sandbox_tool(qrCode, macAddr)
sandboxRes = sandboxEntry.add()
if sandboxRes:
    testRes_2D[0][5] = True
else:
    print("Failed at add_row")
    sys.exit()

for i in currentOtii.otiiList:
    i.set_main(False)


# Start test
input("Please remove j-tag connector, then press enter to start test\n")
test_start_time = datetime.now()

for i in currentOtii.otiiList:
    i.set_main(True)



input("Press ENTER when board goes back to sleep")
# sleep current measurements


sleepCurrentResultList = []
for i in currentOtii.otiiList:
    result = currentOtii.currentMeasurement(i, 10, 0.00001)
    sleepCurrentResultList.append(result)

for i in sleepCurrentResultList:
    if i :
        testRes_2D[0][7] = True
    else:
        print("Failed at sleep")
        sys.exit()

for i in currentOtii.otiiList:
    i.set_main(False)


# check multitenant result
batRes = sandboxEntry.checkHistory("bat", test_start_time)
if batRes != -1:
    testRes_2D[0][6] = True
else:
    print("Failed at bat test")
    sys.exit()

for i in testRes_2D:
    if i[0] == True and i[1] == True and i[2] == True and i[3] == True and i[4] == True and i[5] == True and i[6] == True and i[7] == True:
        brdDatabase.add_Info()
        print("Passed all the test!")
        
print(testRes_2D)