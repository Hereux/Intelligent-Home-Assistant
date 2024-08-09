import requests

wled = "http://desktop-led.local"

presets = {"default": 1, "alert": 3}


class WLED:
    def __init__(self):
        super().__init__()
        self.leds_count = None
        self.brightness = None
        self.get_info()
        self.get_state()

    def set_brightness(self, brightness: int):
        requests.post(wled + "/json", json={"bri": brightness})

    def set_color(self, color: str):
        requests.post(wled + "/json", json={"color": color})

    def set_effect(self, effect: str):
        requests.post(wled + "/json", json={"effect": effect})

    def set_power(self, power: bool):
        requests.post(wled + "/json", json={"on": power})

    def set_preset(self, preset: int, brightness: int = None):
        requests.post(wled + "/json", json={"preset": preset, "bri": brightness})

    def set_intruder_alarm(self):
        print(self.leds_count)
        self.set_preset(1, brightness=255)

    def get_state(self):
        info = requests.get(wled + "/json/state").json()
        self.brightness = info["bri"]
        return info

    def get_info(self):
        info = requests.get(wled + "/json/info").json()
        self.leds_count = info["leds"]["count"]


dwled = WLED()
dwled.set_intruder_alarm()
