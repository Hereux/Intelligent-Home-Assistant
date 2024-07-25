import struct


class CheckForWakeWord:
    def __init__(self):
        self.wakeWordFound = False

    def check_for_wakeword(self, porcupine, pcm):
        self.wakeWordFound = False
        pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(pcm_unpacked)

        if keyword_index >= 0:
            self.wakeWordFound = True
            return self.wakeWordFound
