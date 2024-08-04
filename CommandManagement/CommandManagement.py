import json
import socket
import subprocess
import threading

import colorlog

logger = colorlog.getLogger("AIVoiceAssistant_HX")

from CommandManagement import SoundControl, DisplayControl


# TuyaSmart


def writetojson(variable, value):
    with open("bin/settings.json", mode="r") as read:  # Öffnet die angegebene Datei im Lesemodus
        jsonfile = json.load(read)  # Liest die Datei aus

        with open("bin/settings.json", mode="w") as write:  # Öffnet die Datei im Schreibmodus
            jsonfile[variable] = value
            json.dump(jsonfile, write, ensure_ascii=False, indent=4)  # Speichert die abgeänderte Datei


class CommandManagement(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.is_running = True
        self.last_command = None
        self.soundcontrol = SoundControl.SoundControl()
        self.displaycontrol = DisplayControl.DisplayControl()
        #self.TuyaSmart = TuyaSmart.TuyaSmart()

    def execute_command(self, command: str, conn: socket.socket):
        slot1 = None
        slot2 = None
        utter_message = None
        if not command:
            logger.warning("Kein Befehl erhalten")
            return "mistake"
        elif command.__contains__("action_"):
            command = command.split("action_")[1]

        if command.__contains__("||"):
            splt = command.split("||")
            command = splt[0]
            slot1 = splt[1]
            if len(splt) >= 3:
                slot2 = splt[2]

        command = self.confirmation_exceptions(command)

        if command == "stop":
            self.is_running = False
        elif command == "volume_up":
            self.soundcontrol.louder_volume()
        elif command == "volume_down":
            self.soundcontrol.quieter_volume()
        elif command == "volume_mute":
            self.soundcontrol.mute_volume()
        elif command == "volume_set":
            self.soundcontrol.set_volume(vol=slot1)
        elif command == "volume_get":
            volume = self.soundcontrol.get_volume()
            utter_message = str(volume).strip().lstrip()
        elif command == "change_sound_output":
            self.soundcontrol.change_output_device(device=slot1)
        elif command == "display_on_off":
            utter_message = self.displaycontrol.display_on_off(cmd=slot2, display=slot1)
        elif command == "display_brightness":
            utter_message = self.displaycontrol.display_brightness(brightness=slot2, display=slot1)
        else:
            utter_message = self.addons(command)
        self.last_command = command

        if utter_message:
            logger.info(f"Senden: {utter_message}")
            return utter_message
        else:
            return "None"

    def addons(self, addon: str):
        addons = json.load(open("bin/addons.json", mode="r"))
        try:
            found_addon = addons[addon]
            pass
        except KeyError:
            return addon

        if not any(found_addon):
            logger.error("Addon nicht konfiguriert.")
            return None

        if found_addon["url"]:
            pass

        if found_addon["path"]:
            if found_addon["subprocess"] is True:
                subprocess.Popen(found_addon["path"], shell=True)
            else:
                subprocess.Popen(found_addon["path"], shell=True).wait()
            return found_addon["utter_message"]

    def confirmation_exceptions(self, command: str):
        """
        Dieser Teil ist Hardcoded und wird für außergewöhnliche Fälle verwendet.
        :param command:
        :return:
        """
        print(f"Last Command: {self.last_command}")
        utter_message = command

        if self.last_command and command in ["confirmation_yes", "confirmation_no"] is None:
            return "mistake"

        if command == "confirmation_yes":
            # Hardcode the exceptions
            if self.last_command == "goodbye":
                utter_message = self.last_command + "_yes"

        if command == "confirmation_no":
            # Hardcode the exceptions
            if self.last_command == "goodbye":
                utter_message = self.last_command + "_no"

        self.last_command = None
        if utter_message in ["confirmation_yes", "confirmation_no"]:
            return "mistake"
        return utter_message
