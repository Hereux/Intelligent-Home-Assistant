# Author: Hereux
import json
from threading import Thread

import colorlog
import elevenlabs
import pvporcupine
import pyaudio
import text2numde
from vosk import Model, SpkModel, KaldiRecognizer, SetLogLevel

from SpeechToText import TextToCommands
from SpeechToText.SpeechToText import SpeechToText
from TextToSpeech import TextToSpeech
from WakeWords.CheckForWakeWord import CheckForWakeWord
from bin import SocketServer, utils
from bin.rasa import SendCommand

settings = json.load(
    open("bin/settings.json", "r", encoding="utf-8")
)
access_key = settings["porcupine_access_key"]
spk_model_path = settings["spk_model_path"]
model_path = settings["vosk_model"]
live_speaking = bool(settings["live_speaking"])
using_internet = not bool(settings["offline_mode"])
vosk_log_level = int(settings["vosk_log_level"])
SetLogLevel(vosk_log_level)
logger = colorlog.getLogger("AIVoiceAssistant_HX")
logger.setLevel(colorlog.DEBUG)
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s %(reset)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }
))
logger.addHandler(handler)
logger.info("Starting...")
BLUE = '\033[94m'
GREEN = '\033[92m'
RESET = '\033[0m'  # Zurück zur Standardfarbe


class HomeAssistant:
    """
    Die Klasse HomeAssistant ist die Hauptklasse des Programms. Sie ist für die Steuerung des Programms zuständig.
    Der HomeAssistant hört auf ein Wakeword, erkennt den gesprochenen Text und führt dann den entsprechenden Befehl aus.
    Das Programm befindet sich mitten in der Entwicklungsphase und wird ständig weiterentwickelt.
    Powered by Hereux. All rights reserved!
    """

    def __init__(self):
        super().__init__()
        self.using_rasa = bool(settings["using_rasa"])
        self.is_running = True
        self.kaldi_recognizer = None
        self.audio_stream = None
        utils.__write_to_txt__("", reset=True)
        self.audio_file_gen_process = None
        self.memory = {}

        elevenlabs.set_api_key(settings["elevenlabs_api_key"])
        self.pa = pyaudio.PyAudio()
        self.porcupine = pvporcupine.create(
            access_key=f'{access_key}',
            keyword_paths=["WakeWords/CustomKeywords/Glados_de_windows_v3_0_0.ppn"],
            model_path="WakeWords/porcupine_params_de.pv",
            sensitivities=[1],
        )
        self.cww = CheckForWakeWord()
        self.stt = SpeechToText()
        self.ttc = TextToCommands.TextToCommands()
        self.tts = TextToSpeech.TextToSpeech(live_speaking=live_speaking, using_internet=using_internet)
        self.server = SocketServer.Server()
        self.server.start()

        s2t_model = Model(model_path)
        speaker_model = SpkModel(spk_model_path)
        self.kaldi_recognizer = KaldiRecognizer(s2t_model, 16000, speaker_model)
        self.speakers = self.__get_speakers__()
        utils.writetojson("settings", "speakers", self.speakers)

    def __get_speakers__(self):
        """
        Gibt eine gefilterte Liste aller Lautsprecher zurück.
        :return: List[device_info.get("name")]
        """
        speakers = []
        for device_count in range(self.pa.get_device_count()):
            device_info = self.pa.get_device_info_by_index(device_count)
            # Filter unwanted audio drivers
            if device_info.get("hostApi") != 2:
                continue

            # Filter microphones
            if device_info.get("maxInputChannels") != 0:
                continue
            speakers.append(device_info.get("name"))

        return speakers

    def get_audio_stream(self):  # Startet den Audio Stream
        """
        Startet den Audio Stream von Porcupine.
        :return: type: Stream
        """
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
            input_device_index=self.pa.get_default_input_device_info().get("index"),
        )

    def when_missing_audio_files(self):
        if self.audio_file_gen_process is None:
            print("Starting thread")
            missing_data = self.memory["missing_data"] = self.tts.missing_data
            self.audio_file_gen_process = Thread(target=self.tts.generate_audio_files, args=(missing_data,))
            self.audio_file_gen_process.start()

        elif self.audio_file_gen_process.is_alive() is False:
            print("THREAD IS DEAD")
            self.tts.should_listen_after_playing = self.tts.should_listen_after_generating
            self.tts.should_listen_after_generating = False
            self.tts.is_missing_files = False
            self.audio_file_gen_process = None

            missing_memory = self.memory["missing_data"]
            lds, exists = self.tts.get_command_path(missing_memory[0], missing_memory[2])
            if exists:
                self.tts.elevenlabs_module(command=missing_memory[0], entities=missing_memory[1])
            else:
                print("Error: File still missing.")

            self.memory.clear()

    def manual_ttc(self, sentence: str):
        """
        Findet einen passenden Befehl und gibt den Befehlsnamen, die Entities und die Antwort zurück.
        :param sentence: Der User Input.
        :return: None
        """
        command, response, entities = self.ttc.manual_text_to_commands(sentence)
        utils.__write_to_txt__(f"{command}|{entities}|{response}")

        if command == "error":
            logger.error("Fehler mit dem ausführenden Befehlsclient.")
            return command, None, None
        return command, entities, response

    @staticmethod
    def send_command_to_client(command: str, entities: list, response: str):
        """
        Sendet den Befehl an den Client und gibt die Antwort zurück.
        :param command: Die Befehlsbezeichnung.
        :param entities: Die Daten.
        :param response: Die Antwort auf den Befehl.
        :return: Die Antwort auf den Befehl, ggf. mit ergänzten Werten.
        """
        received_data = None
        if not entities or len(entities) == 0:
            received_data = SendCommand.send_to_server(command=command)
        elif len(entities) == 1:
            received_data = SendCommand.send_to_server(command=command, slot1=entities[0])
        elif len(entities) == 2:
            received_data = SendCommand.send_to_server(command=command, slot1=entities[0],
                                                       slot2=entities[1])

        return received_data if received_data is not None else response

    def text_to_speech(self, command: str, entities: list, response: str):
        if live_speaking is True:
            self.tts.pytts3_module(response)
        else:
            self.stt.is_listening = self.tts.elevenlabs_module(command=command, entities=entities)

    def start(self):

        logger.info("GladOS wurde erfolgreich hochgefahren.")
        entities = None
        command = None

        self.get_audio_stream()  # Starte Audio Stream
        while self.is_running:
            try:
                # Lese Audio Stream
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                self.cww.check_for_wakeword(porcupine=self.porcupine, pcm=pcm)

                if self.tts.is_missing_files:
                    print(self.tts.is_missing_files)
                    self.when_missing_audio_files()

                if self.cww.wakeWordFound or self.tts.should_listen:
                    self.tts.play_sound("sound_effects\\portal_button_on.wav")
                    self.stt.is_listening = True
                if not self.stt.is_listening:
                    continue

                #  Hört dem Audiostream zu und wandelt Sprache in Text um
                self.tts.should_listen = False
                self.stt.listen(pcm=pcm, kaldi_recognizer=self.kaldi_recognizer)

                if self.stt.is_listening is not False:
                    continue

                # Wenn Recognizer fertig ist, wird überprüft, ob ein Text erkannt wurde
                sentence: str = self.stt.result_sentence
                if sentence.encode("utf-8") == b'':
                    logger.info("Kein Text erkannt.")
                    self.tts.play_sound("sound_effects\\portal_button_off.wav")
                    continue

                sentence = text2numde.sentence2num(sentence)
                logger.info("Sprache zu Text umgewandelt; Text: " + sentence)

                # BEFEHLS-ERKENNUNG
                if self.using_rasa:
                    response = self.ttc.get_rasa_response(sentence=sentence)
                    print("RASA Response: " + response)
                else:
                    command, entities, response = self.manual_ttc(sentence)

                # BEFEHLS-AUSFÜHRUNG
                command = self.send_command_to_client(command, entities, response)
                print("Command: " + command)
                # SPRACH-AUSGABE
                self.text_to_speech(command, entities, response)

            except KeyboardInterrupt or SystemExit:
                logger.info("Home Assistant stopping...")
                HomeAssistant.stop(self)
                break

    def stop(self):
        self.server.stop_server()
        self.audio_stream.close()
        self.pa.terminate()
        self.porcupine.delete()
        print("Home Assistant stopped")

        self.is_running = False

        return


if __name__ == '__main__':
    home_assistant = HomeAssistant()
    home_assistant.start()

# Info: Tonausgabe nicht über Bluetooth möglich
# Todo: Sauberer Stopp des Programms
