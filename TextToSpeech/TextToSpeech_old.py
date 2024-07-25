
filtered_responses = {
    "utter_error": [
        "Es ist ein Fehler aufgetreten.", "Es ist ein Problem mit der Befehlsverarbeitung aufgetreten.",
        "Ich habe dich nicht verstanden."
    ]
}
for key, value in responses.items():
    filtered_texts = []
    for ttext in value:
        ttext = ttext["text"]
        filtered_text = re.sub(r"\{[^}]+\}", '', ttext).replace("  ", " ")

        filtered_texts.append(filtered_text.strip().encode("utf-8").decode("utf-8"))
    filtered_responses[key] = filtered_texts

utils.writetojson("settings", "filtered_responses", filtered_responses)


class TextToSpeech:
    def __init__(self, live_speaking=True, using_internet=True, output_device=None):
        self.missing_data = None
        self.is_running = False
        self.is_speaking = False
        self.is_missing_files = False  # Wird auf True gesetzt, wenn eine Audiodatei noch nicht generiert wurde
        self.should_listen = False  # Wird auf True gesetzt wenn der Text gesprochen wurde.
        self.should_listen_after_playing = False  # Wird auf True gesetzt, wenn der Text zuvor ein § enthält
        self.using_internet = using_internet
        self.found_entities: list = []
        self.indexes: list = []
        self.text_variant = 0
        self.texts: list = []
        self.index = -1
        self.output_device = output_device

        if live_speaking:
            logger.debug("Live Speaking is enabled.")
            engine = pyttsx3.init()
            # Set Rate
            engine.setProperty('rate', 190)
            # Set Volume
            engine.setProperty('volume', 1.0)
            # Set Voice (Female)
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[0].id)
            self.engine = engine
        else:
            self.settings = json.load(open("bin/settings.json", "r", encoding="utf-8"))
            self.main_dir_path = os.path.join(os.getcwd(), "bin", "ElevenLabsAudioFiles",
                                              self.settings["elevenlabs_voice_name"])
            self.missing_audio_files_path = os.path.join(self.main_dir_path, "missing_audio_files")

            if not os.path.exists(self.main_dir_path):
                os.makedirs(self.main_dir_path)
            number_path = os.path.join(self.main_dir_path, "numbers")
            if not os.path.exists(number_path):
                os.makedirs(number_path)

    def play_sound(self, path):
        """
        Spielt eine Audiodatei ab.
        :param path: Der relative Pfad zur Audiodatei
        :return: None
        """
        path = os.path.join(os.getcwd(), "bin", path)

        def __thread__():
            sound = AudioSegment.from_mp3(path)
            play(sound, output_device=self.output_device)

        threading.Thread(target=__thread__).start()

    def __filter_nums__(self, word):
        """
        Filter function. If a word is a number, it will be appended on the found_entities list and returns the number.
        :param word: The word to be scanned.
        :return: String or Integer.
        """
        self.index += 1

        if not word.isdigit():
            return False
        number = int(word)
        self.found_entities.append(number)
        self.indexes.append(self.index)
        return True

    def __split_entities__(self, text: str):
        ret_text = text
        pos = []
        for word in text.split():
            if word.isdigit():
                self.found_entities.append(int(word))
                ret_text = ret_text.replace(word, "", 1)
                ret_text = ret_text.replace("  ", " ")

            else:
                retword, is_bool = utils.__split_boolean__(word)
                if is_bool is not None:
                    self.found_entities.append(is_bool)
                    ret_text = ret_text.replace(word, retword, 1)
                    ret_text = ret_text.replace("  ", " ")
        return ret_text

    def __get_command_path__(self, text, command: str = None):
        """
        Sucht mit dem gegebenen Text nach einem passenden Befehlsnamen. Mit diesem Begriff wird der Pfad der
        Audiodateien gefunden.
        :param text: Der gewünschte Text
        :return: Liste mit Pfaden zu den Audiodateien
        """

        if command is None:
            logger.debug("Es wurde kein Command und keine Entities übergeben.")
            search_text = self.__split_entities__(text)
            print("Search Text: ", search_text)
            command = [test for test in filtered_responses if search_text in filtered_responses[test]]
            command = command[0]  # entfernt nur die Klammern
            text_variant = filtered_responses[command].index(search_text) + 1  # Welche der verschiedenen Audio-Dateien
        else:
            command = "utter_" + command
            text_variant = random.randint(0, len(filtered_responses[command])) + 1
            # Welche der verschiedenen Audio-Dateien

        command_path = os.path.join(self.main_dir_path, command)  # Path zu dem Verzeichnis des Befehls
        chosen_command_path = os.path.join(command_path, str(text_variant))  # Path zu dem ausgewählten Befehl

        # Falls der Pfad vom Befehl nicht existiert, wird er erstellt
        if not os.path.exists(command_path):
            os.makedirs(command_path)

        # Falls der Pfad vom ausgewählten Befehl nicht existiert, wird er erstellt
        if not os.path.exists(chosen_command_path):
            os.makedirs(chosen_command_path)
            return chosen_command_path, False
        # Falls die Audio-Dateien nicht existieren, wird der Pfad zurückgegeben
        elif not os.listdir(chosen_command_path):
            return chosen_command_path, False

        # Falls die Audio-Dateien existieren, wird der Pfad zurückgegeben
        return chosen_command_path, True

    def __elevenlabs_get_audio_files__(self, command_path):
        """
        Sucht nach den Audiodateien und gibt sie zurück.
        :param: command_path: Der Pfad zu dem Überordner mit den Audiodateien.
        :return: Gibt eine Liste mit den passenden Pfaden zu den Audiodateien zurück.
        """
        text_audio_files = os.listdir(command_path)  # Liste mit den Texten zwischen den Zahlen
        text_audio_files_len = len(text_audio_files) + len(self.found_entities)  # Anzahl der Audiodateien
        audio_files = []  # Liste mit den Pfaden von Texten und Zahlen

        #  Iteriert abwechselnd über die Texte und Nummern und fügt sie in die finale Liste hinzu
        number = False
        for index in range(text_audio_files_len):
            if index >= len(text_audio_files): index -= 1

            if not number:
                number = True
                path = os.path.join(command_path, str(text_audio_files[index]))
                audio_files.append(path)
                continue
            else:
                number = False
                path = os.path.join(self.main_dir_path, "numbers", str(self.found_entities[0]) + ".mp3")
                audio_files.append(path)
                self.found_entities.pop(0)
                continue

        logger.debug(f"Finished getting audio files {audio_files}")
        return audio_files

    def pytts3_module(self, text):
        """Used to pytts3_module whatever response_text is passed to it"""

        if text.__contains__("§"):
            self.should_listen = True
            text = text.replace("§", "")

        self.engine.say(text)
        self.engine.runAndWait()

    def elevenlabs_generate_audio_files(self, data):
        """
        Wird ausgeführt um Audiodateien von ElevenLabs zu generieren.
        :return: None
        """
        command, entities, response_text, command_path = data

        if not self.using_internet or not utils.check_for_internet():
            self.elevenlabs_module(
                response_text="Kritischer Systemfehler. Das Internet ist deaktiviert oder nicht erreichbar.")
            logger.debug("Internet ist deaktiviert oder nicht erreichbar.")
            return False

        for count in range(len(texts)):
            text = texts[count]

            if text.__contains__("§"): text = text.replace("§", "")
            logger.info("Generiere: " + texts[count])

            path = os.path.join(command_path, str(count + 1) + ".mp3")

            voice = elevenlabs.generate(voice=self.settings["elevenlabs_voice_id"], text=text,
                                        model="eleven_multilingual_v2")
            elevenlabs.save(voice, path)

            # Spielt die neu generierte Audiodatei ab
            print("Playing: ", path)
            self.elevenlabs_module(response_text=response_text)

    def __elevenlabs_speak_thread__(self, audio_files, end_cut=100):
        """
        Die Funktion, die den Text ausspricht.
        :param audio_files: Eine Liste in denen die Pfade zu den Audiodateien sind.
        :return:
        """
        logging.getLogger("AIVoiceAssistent_HX")
        logger.debug(f"Starting to speak; {self.is_speaking}")
        while self.is_speaking:  # Wartet bis die Audiodateien abgespielt wurden
            continue

        self.is_speaking = True
        # Spielt die Audiodateien in Reihenfolge ab
        for song in audio_files:
            sound = AudioSegment.from_mp3(song)
            play(sound[:len(sound) - end_cut])
        self.is_speaking = False

        # Soll erst zuhören, wenn die jetzt generierten Audiodateien abgespielt wurden
        if not self.is_missing_files:
            self.should_listen = self.should_listen_after_playing

        if not self.should_listen or self.is_missing_files:
            self.play_sound("sound_effects\\portal_button_off.wav")

        time.sleep(0.5)
        self.__reset__()
        return

    def __elevenlabs_speak__(self, audio_paths):
        thread = threading.Thread(target=self.__elevenlabs_speak_thread__, args=(audio_paths,))
        thread.start()

    def __reset__(self):
        self.is_missing_files = False
        self.found_entities: list = []
        self.indexes: list = []
        self.text_variant = 0
        self.texts: list = []
        self.index = -1
        return

    def elevenlabs_module(self, command: str = None, entities: list = None, response_text: str = None):
        """
        Wird ausgeführt um Dateien von ElevenLabs abzuspielen.

        :param command: Bei manueller Textverarbeitung wird der Befehl mit übergeben.
        :param entities: Bei manueller Textverarbeitung werden die Entities mit übergeben.
        :param response_text: Der Text der gesprochen werden soll
        :return: True wenn eine Antwort erwartet wird und False wenn nicht
        """
        self.__reset__()
        self.should_listen_after_playing = response_text.__contains__("§")
        logger.warning(f"elevenlabs_module: {command, entities, response_text}")

        command_path, exists = self.__get_command_path__(response_text, command)
        # Wenn es keine Audiodateien gibt, dann werden welche hinzugefügt
        if exists is False:
            logger.info(f"Es gibt keine Audiodateien. | {command_path}")
            self.is_missing_files = True
            self.missing_data = [command, entities, response_text, command_path]

            # Spielt eine zufällige Audiodatei ab, die sagt, dass die Audiodateien noch nicht generiert wurden.
            file_missing_audio = self.missing_audio_files_path
            chosen_command = random.randint(1, len(os.listdir(file_missing_audio)))
            command_path = os.path.join(file_missing_audio, str(chosen_command))

        elif exists is None:
            logger.error("Fehler")
            return False

        audio_files = self.__elevenlabs_get_audio_files__(command_path)
        self.__elevenlabs_speak__(audio_files)

