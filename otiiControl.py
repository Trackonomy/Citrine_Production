import example_config as cfg
from otii_tcp_client import otii, otii_connection
import time

class activeProj():
    def __init__(self, plotFlag = True) -> None:
        self.connection = otii_connection.OtiiConnection(cfg.HOST["IP"], cfg.HOST["PORT"])
        self.connect_response = self.connection.connect_to_server()
        if self.connect_response["type"] == "error":
            print("Exit! Error code: " + self.connect_response["errorcode"] + ", Description: " + self.connect_response["data"]["message"])
        self.otii_object = otii.Otii(self.connection)
        devicesList = self.otii_object.get_devices()
        self.otiiList = sorted(devicesList, key=lambda x: x.name)
        self.proj = self.otii_object.get_active_project()
        self.plotFlag = plotFlag
        if self.plotFlag == True:
            self.recording = self.proj.start_recording()

    def currentMeasurement(self, otiiName: str, seconds: int, threshold: float) -> bool:
        self.recording = self.proj.start_recording()
        self.recording = self.proj.get_last_recording()
        time.sleep(seconds)
        self.proj.stop_recording()
        count = self.recording.get_channel_data_count(otiiName.id, "mc")
        data = self.recording.get_channel_data(otiiName.id, "mc", 0, count)
        avgvalue = sum(data['values']) / len(data['values'])
        if abs(avgvalue) < abs(threshold):
            print(f"device {otiiName} current test: PASSED, its sleep current: {avgvalue}")
            return True
            # return_dict[deviceNum].append(True)
        else:
            print(f"device {otiiName} current test: FAILED, its sleep current: {avgvalue}")
            return False
