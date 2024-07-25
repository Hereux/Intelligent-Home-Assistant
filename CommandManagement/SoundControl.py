import time
from ctypes import cast, POINTER

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))


class SoundControl:
    def __init__(self):
        pass

    @staticmethod
    def set_volume(vol: str):
        old_volume = int(round(volume.GetMasterVolumeLevelScalar() * 100))
        vol = int(vol)

        if vol < 0:
            vol = 0
        elif vol > 100:
            vol = 100

        if vol > old_volume:
            for v in range(old_volume, vol):
                scalarvolume = vol / 100
                volume.SetMasterVolumeLevelScalar(scalarvolume, None)
                time.sleep(0.05)
        else:
            for vol in range(old_volume, vol, -1):
                scalarvolume = vol / 100
                volume.SetMasterVolumeLevelScalar(scalarvolume, None)
                time.sleep(0.05)
        scalarvolume = vol / 100
        volume.SetMasterVolumeLevelScalar(scalarvolume, None)
        return

    def louder_volume(self):
        old_vol = int(round(volume.GetMasterVolumeLevelScalar() * 100))
        new_vol = str(old_vol + 10)
        self.set_volume(new_vol)

    def quieter_volume(self):
        old_vol = int(round(volume.GetMasterVolumeLevelScalar() * 100))
        new_vol = str(old_vol - 10)
        self.set_volume(new_vol)

    def change_output_device(self, device: str):
        print("Change output device to: ", device)
        pass

    @staticmethod
    def mute_volume():
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            vol = session._ctl.QueryInterface(ISimpleAudioVolume)
            if vol.GetMute() == 0:
                vol.SetMute(True, None)
            else:
                vol.SetMute(False, None)

    @staticmethod
    def get_volume():
        return int(round(volume.GetMasterVolumeLevelScalar() * 100))

