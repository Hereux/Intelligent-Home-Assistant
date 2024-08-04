import os
import time

from screeninfo import get_monitors

from bin.utils import rreplace

monitors = len(get_monitors())


class DisplayControl:
    def __init__(self):
        super().__init__()

    @staticmethod
    def __change_brightness_smooth__(display: int, old_brightness: int, new_brightness: int) -> None:
        brightness_step = 7
        if new_brightness < old_brightness:
            brightness_step = brightness_step.__invert__()

        for i in range(old_brightness, new_brightness, brightness_step):
            os.popen(f'ControlMyMonitor.exe /ChangeValue "\\\.\DISPLAY{display}\Monitor0" 10 {brightness_step}')
            time.sleep(0.1)
        return None

    def execute(self, cmd, display):
        if cmd == "aus":
            os.system(f'ControlMyMonitor.exe /SetValue "\\\.\DISPLAY{display}\Monitor0" D6 4"')
        elif cmd == "an":
            os.system(f'ControlMyMonitor.exe /SetValue "\\\.\DISPLAY{display}\Monitor0" D6 1"')
        elif cmd == "heller":
            old_brightness = int(os.popen(f'bin\get_brightness.bat {display}').read())
            print("old", old_brightness)

            self.__change_brightness_smooth__(display=display, old_brightness=old_brightness,
                                              new_brightness=old_brightness-30)
            return
        elif cmd == "dunkler":
            old_brightness = int(os.popen(f'bin\get_brightness.bat {display}').read())

            self.__change_brightness_smooth__(display=display, old_brightness=old_brightness,
                                              new_brightness=old_brightness-30)
            return

        elif cmd:
            try:
                brightness = int(cmd)
            except:
                print("Ich konnte die Helligkeit nicht verstehen.")
                return "Ich konnte die Helligkeit nicht verstehen."
            old_brightness = int(os.popen(f'bin\get_brightness.bat {display}').read())

            self.__change_brightness_smooth__(display=display, old_brightness=old_brightness, new_brightness=brightness)
            return
        else:
            return "Ich konnte dich leider nicht verstehen."

    def display_on_off(self, cmd, display):
        if not cmd or not display:
            print("Ich konnte dich leider nicht verstehen. DisplayControl")
            return
        if cmd.__contains__("1"):
            cmd = rreplace(cmd, "1", "ein", 1)

        if display == "alle":
            for dis in range(1, monitors + 1):
                self.execute(cmd, dis)
            return
        else:
            self.execute(cmd, display)
            return

    def display_brightness(self, brightness, display):
        if brightness and display == "alle":
            for dis in range(1, monitors + 1):
                self.execute(brightness, dis)
            return

        elif brightness and display:
            self.execute(brightness, display)
            return
        else:
            return
