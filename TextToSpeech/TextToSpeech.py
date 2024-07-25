import json
import logging
import os
import random
import re

import pyttsx3
import yaml
from multiprocess import Process
from pydub import AudioSegment
from pydub.playback import play

from bin import utils
from bin.utils import alternate_lists

logger = logging.getLogger("AIVoiceAssistant_HX")

domain = yaml.load(open("bin/rasa/domain.yml", "r", encoding="utf-8"), Loader=yaml.Loader)
responses = domain["responses"]

filtered_responses = {
    "utter_error": [
        "Es ist ein Fehler aufgetreten.", "Es ist ein Problem mit der Befehlsverarbeitung aufgetreten.",
        "Ich habe dich nicht verstanden."
    ]
}


def initalize_command_data():
    """
    Lädt die Befehlsdaten aus der Domain Datei in ein Dictionary
    :return: Ein Dictionary mit den Befehlsdaten
    """
    for key, value in responses.items():
        filtered_texts = []
        for ttext in value:
            ttext = ttext["text"]
            filtered_text = re.sub(r"\{[^}]+\}", '', ttext).replace("  ", " ")

            filtered_texts.append(filtered_text.strip().encode("utf-8").decode("utf-8"))
        key = key.replace("utter_", "")
        filtered_responses[key] = filtered_texts

    utils.writetojson("settings", "filtered_responses", filtered_responses)
    return filtered_responses


def initialize_pyttsx3():
    """
    Initialisiert die pyttsx3 Engine.
    :return: Initialisierte pyttsx3 Engine.
    """
    logger.debug("Live Speaking is enabled.")
    engine = pyttsx3.init()
    engine.setProperty('rate', 190)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    return engine


def initialize_audio_folders(settings: dict):
    """
    Initialisiert die Ordner für die Audiodateien.
    :return: Hauptverzeichnis der Audiodateien und fehlende Audiodateien-Verzeichnis.
    """
    main_dir_path = os.path.join(os.getcwd(), "bin", "ElevenLabsAudioFiles", settings["elevenlabs_voice_name"])
    missing_audio_files_path = os.path.join(main_dir_path, "missing_audio_files")

    if not os.path.exists(main_dir_path):
        os.makedirs(main_dir_path)

    number_path = os.path.join(main_dir_path, "numbers")
    if not os.path.exists(number_path):
        logger.warning("Keine generierten Zahlen Audiodateien gefunden.")
        os.makedirs(number_path)

    special_entities_path = os.path.join(main_dir_path, "special_entities")
    if not os.path.exists(special_entities_path):
        logger.warning("Keine generierten Spezial Entitäten Audiodateien gefunden.")
        os.makedirs(special_entities_path)

    return main_dir_path, missing_audio_files_path, number_path, special_entities_path


class TextToSpeech:
    def __init__(self, live_speaking=True, using_internet=True, output_device=None):
        self.missing_data = None
        self.is_running = False
        self.is_speaking = False
        self.is_missing_files = False  # Wird auf True gesetzt, wenn eine Audiodatei noch nicht generiert wurde
        self.should_listen = False  # Wird auf True gesetzt wenn der Text gesprochen wurde.
        self.should_listen_after_playing = False  # Wird auf True gesetzt, wenn der Text zuvor ein § enthält
        self.should_listen_after_generating = False  # Wird auf True gesetzt, wenn noch Text generiert werden muss der
        # & enthält
        self.using_internet = using_internet
        self.found_entities: list = []
        self.indexes: list = []
        self.text_variant = 0
        self.texts: list = []
        self.index = -1
        self.output_device = output_device
        self.command_data = initalize_command_data()
        self.settings = json.load(open("bin/settings.json", "r", encoding="utf-8"))

        if live_speaking:
            self.engine = initialize_pyttsx3()
            return
        self.main_dir_path, self.missing_audio_files_path, self.number_path, self.special_entities_path = \
            initialize_audio_folders(self.settings)

    def play_sound(self, path, blocking=False, end_cut=0):
        """
        Spielt eine Audiodatei ab.
        :param path: Der relative Pfad zur Audiodatei.
        :param blocking: Ob der Code blockiert werden soll.
        :param end_cut: Der Wert in Millisekunden, um den die Audiodatei gekürzt werden soll.
        :return: None
        """
        path = os.path.join(os.getcwd(), "bin", path)

        def __process__():
            self.is_speaking = True
            sound = AudioSegment.from_mp3(path)
            play(sound[:len(sound) - end_cut])
            self.is_speaking = False

            if self.should_listen_after_playing:
                self.should_listen = True
                self.should_listen_after_playing = False
        if blocking:
            __process__()
        else:
            print("Not Blocking")
            proc = Process(target=__process__)
            proc.start()

    def pytts3_module(self, text):
        """
        Spricht den Text aus. Blockiert allerdings den Code.
        :param text: Der Text, der gesprochen werden soll.
        :return: None
        """
        if text.__contains__("§"):
            self.should_listen = True
            text = text.replace("§", "")
        self.engine.say(text)
        self.engine.runAndWait()
        return None

    def get_command_path(self, command, command_index):
        """
        Gibt den Pfad zu den Audiodateien zurück.
        :param command: Der Befehl.
        :param command_index: Welche Variante des Befehls.
        :return: Befehlsverzeichnis u. ob es existiert.
        """

        command_dir = os.path.join(self.main_dir_path, command, str(command_index+1))
        exists = os.path.exists(command_dir)
        return command_dir, exists

    def play_missing_files_sound(self):
        """
        Spielt eine Audiodatei ab, die darauf hinweist, dass eine Audiodatei fehlt und generiert wird.
        :return: None
        """

        audio_files = self.command_data["missing_audio_files"]
        audio_file = random.choice(audio_files)
        self.play_multiple_files([], audio_file, blocking=False)
        return None

    def identify_entity(self, entity, command_dir):
        """
        Identifiziert die Entität.
        :param command_dir: Der Pfad zum Befehlsverzeichnis.
        :param entity: Die Entität.
        :return: None
        """
        if entity.isdigit():
            return str(entity), self.number_path
        if entity in ["ein", "an", "aus"]:
            return str(entity), self.special_entities_path
        return str(entity), command_dir

    def play_multiple_files(self, entities: list, command_dir, blocking=False, end_cut=0) -> None:
        """
        Spielt mehrere Audiodateien ab.
        :param entities: Die Liste mit den Entitäten.
        :param command_dir: Der Pfad zu den Audiodateien.
        :param end_cut: Der Wert in Millisekunden, um den die Audiodatei gekürzt werden soll.
        :param blocking: Ob der Code blockiert werden soll.
        :return: None
        """
        command_files = os.listdir(command_dir)
        command_files_paths = [os.path.join(command_dir, file) for file in command_files]
        entity_paths = []

        for entity in entities:
            entity, path = self.identify_entity(entity, command_dir)
            entity_path = os.path.join(path, entity)
            entity_paths.append(entity_path)

        def __process__():
            self.is_speaking = True
            print(command_files_paths, entity_paths)
            for audio_path in alternate_lists(command_files_paths, entity_paths):

                sound = AudioSegment.from_mp3(audio_path)

                play(sound[:len(sound) - end_cut])
            self.is_speaking = False

        if blocking:
            print("Blocking")
            __process__()
        else:
            print("Not Blocking")
            proc = Process(target=__process__)
            proc.start()

        return None

    def elevenlabs_module(self, command, entities):
        """
        Dieser Code existiert aus folgendem Grund. Texte immer direkt über ElevenLabs zu generieren ist teuer.
        Deshalb werden die Texte in einer Ordnerstruktur gespeichert und nur bei Bedarf neu generiert.
        Die folgende Funktion prüft, ob die Audiodatei bereits existiert. Wenn nicht, wird sie generiert.
        :param command: Die Befehlsbezeichnung.
        :param entities: Die Daten.
        :return:
        """

        if command not in self.command_data:
            logger.error("Befehl ist erkannt worden, ist aber nicht in der Domain Datei vorhanden.")
            return
        command_variations = self.command_data[command]
        response = random.choice(command_variations)
        command_index = command_variations.index(response)

        if response.__contains__("§"):
            self.should_listen_after_playing = True
            response = response.replace("§", "")

        command_dir, exists = self.get_command_path(command, command_index)
        logger.debug(f"Command Dir: {command_dir} | Exists: {exists}")
        if not exists:
            logger.info("Audiodatei existiert nicht. Generiere Audiodatei.")
            self.missing_data = [command, entities]
            self.is_missing_files = True


            # Falls die Audiodatei noch nicht existiert, wird das zuhören verschoben
            self.should_listen_after_generating = self.should_listen_after_playing
            self.should_listen_after_playing = False
            self.play_missing_files_sound()
            return

        self.play_multiple_files(entities, command_dir, blocking=False)