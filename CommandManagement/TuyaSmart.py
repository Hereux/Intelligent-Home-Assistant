import json

from tuya_connector import TuyaOpenAPI

settings = json.load(open("bin/settings.json", "r", encoding="utf-8"))

ACCESS_ID = settings["tuya_access_id"]
ACCESS_KEY = settings["tuya_access_key"]
API_ENDPOINT = "https://openapi.tuyaeu.com"
USERNAME = settings["tuya_username"]
PASSWORD = settings["tuya_password"]

tuya_device_ids = {
    "marc's_zimmer": "012002382c3ae84253d6",
}

tuya_device_infos = {
}


class TuyaSmart:

    def __init__(self):
        super().__init__()
        self.api = TuyaOpenAPI(endpoint="https://openapi-weaz.tuyaeu.com", access_id=ACCESS_ID,
                               access_secret=ACCESS_KEY)
        self.device_index()

    def connect(self):
        self.api.connect()

    def device_index(self):
        for device in tuya_device_ids:
            response = self.api.get("/v1.0/devices/" + tuya_device_ids[device])
            print("deviceindex ", response)
            tuya_device_infos[device] = response

    def lamp_turn_on(self, device="marc's zimmer"):
        commands = {'commands': [{'code': 'switch_led', 'value': True}]}
        request = self.api.post(f'/v1.0/iot-03/devices/{device}/commands', commands)
        print(request)

    def lamp_turn_off(self, device="marc's zimmer"):
        commands = {'commands': [{'code': 'switch_led', 'value': False}]}
        request = self.api.post(f'/v1.0/iot-03/devices/{device}/commands', commands)
        print(request)

