import json

import colorlog
import numpy as numpy

logger = colorlog.getLogger("AIVoiceAssistant_HX")


all_users = json.load(
    open("bin/UserVoices.json", mode="r", encoding="utf-8")
)


def writetojson(variable, value):
    with open("bin/UserVoices.json", mode="r") as read:  # Öffnet die angegebene Datei im Lesemodus
        jsonfile = json.load(read)  # Liest die Datei aus

        with open("bin/UserVoices.json", mode="w") as write:  # Öffnet die Datei im Schreibmodus
            jsonfile[variable] = value
            json.dump(jsonfile, write, ensure_ascii=False, indent=4)  # Speichert die abgeänderte Datei


class SpeechToText:

    def __init__(self):
        super().__init__()
        self.is_listening = False
        self.result_sentence = None
        self.result_user = None
        self.best_speaker = None
        self.best_cosdist = 100

    def get_speaker(self, uservoice):
        for user in all_users:
            user = all_users[user]

            if not user["voices"]:
                continue

            for voice_data in user["voices"]:
                nx = numpy.array(voice_data)
                ny = numpy.array(uservoice)

                # Wenn die Cosinusdistanz kleiner als die bestmögliche Cosinusdistanz ist und den Schwellwert von 0.3
                # überschreitet.
                cosdist = 1 - numpy.dot(nx, ny) / numpy.linalg.norm(nx) / numpy.linalg.norm(ny)
                if cosdist > 0.5:
                    continue
                if cosdist < self.best_cosdist:
                    self.best_cosdist = cosdist
                    self.best_speaker = user["name"]

        # logger.debug(f"Die Cosinusdistanz beträgt: {self.best_cosdist}", f"Der beste Sprecher ist: {self.best_speaker}")
        if self.best_speaker is None:
            all_users["1"]["voices"].append(uservoice)
            writetojson("1", all_users["1"])
        return self.best_speaker

    def listen(self, pcm, kaldi_recognizer):
        user = None
        self.is_listening = True
        # Spracherkennung
        if kaldi_recognizer.AcceptWaveform(pcm):
            reco_result = json.loads(
                kaldi_recognizer.Result()
            )

            # Hole das Resultat aus dem JSON Objekt
            sentence = reco_result['text']
            if reco_result['text'] is None:
                self.result_sentence = None
                self.result_user = None
                self.is_listening = False
                return
            elif "spk" in reco_result:
                voice = reco_result['spk']
                user = SpeechToText.get_speaker(self, voice)

            logger.debug(f'Nutzer: {user}')
            self.is_listening = False

            self.result_sentence = sentence
            self.result_user = user

    def stop_listening(self):
        self.is_listening = False
        self.result_sentence = None
        self.result_user = None
