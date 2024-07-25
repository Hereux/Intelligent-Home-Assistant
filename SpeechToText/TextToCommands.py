import difflib
import json
import random
import re

import colorlog
import requests
import yaml

settings = json.load(
    open("bin/settings.json", "r", encoding="utf-8")
)
headers = {'content-type': 'application/json'}
rasa_adress = settings["rasa_adress"]
ERROR_CODES = settings["filtered_responses"]["utter_error"]


def writetojson(filename, variable, value):
    with open(f"bin/{filename}.json", mode="r") as read:  # Öffnet die angegebene Datei im Lesemodus
        jsonfile = json.load(read)  # Liest die Datei aus

        with open(f"bin/{filename}.json", mode="w") as write:  # Öffnet die Datei im Schreibmodus
            jsonfile[variable] = value
            json.dump(jsonfile, write, ensure_ascii=False, indent=4)  # Speichert die abgeänderte Datei


logger = colorlog.getLogger("AIVoiceAssistant_HX")
BLUE = '\033[94m'
GREEN = '\033[92m'
RESET = '\033[0m'  # Zurück zur Standardfarbe


class TextToCommands:

    def __init__(self):
        super().__init__()

        self.entity_types = {}
        self.commands = {}
        self.current_vars = {}
        self.wrong_words = ["eine", "einen", "einer", "einem", "eines", "nein"]

        nlu_data = self.__read_yaml__("bin/rasa/data/nlu.yml")["nlu"]
        self.domain_data = self.__read_yaml__("bin/rasa/domain.yml")

        if not nlu_data or not self.domain_data:
            raise Exception("No data found.")

        #  Lädt die Entity Typen aus der Domain Datei in ein Dictionary
        sds = {"str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict, "set": set, "tuple": tuple}
        for entity in self.domain_data["entity_types"]:
            entity_name = list(entity.keys())[0]
            entity_type = sds[entity[entity_name]]
            self.entity_types[entity_name] = entity_type

        #  Lädt die Beispieltexte aus der Domain Datei in ein Dictionary
        for index in range(len(nlu_data)):
            item = nlu_data[index]
            intent = item["intent"]
            examples = item["examples"]

            entity_count = examples.count("[")

            examples = re.sub(r"[(\[].*?[)\]]", "", examples)
            examples = examples.replace("\n", "")  # Remove newlines
            examples = examples.strip()  # Remove leading and trailing whitespaces
            examples = examples.replace("  ", " ")  # Remove double whitespaces
            examples = examples.split("- ")  # Convert to list
            del examples[0]  # Remove first element

            entity_count = int(entity_count / len(examples))
            self.commands[intent] = [examples, entity_count]

        domain_responses = self.domain_data["responses"]
        self.command_responses = {}

        # Lädt die Antworten aus der Domain Datei in ein Dictionary
        for intent in domain_responses:
            data = domain_responses[intent]
            response = [res["text"] for res in data]

            intent = intent.replace("utter_", "")
            self.command_responses[intent] = response

    def get_rasa_response(self, sentence: str):
        if not sentence:
            print("No command given.")
            return

        try:
            payload = {
                "sender": "Marc's PC",
                "message": sentence
            }
            r = requests.post("http://localhost:5005/webhooks/rest/webhook", json=payload, headers=headers)
            response = r.json()[0]["response_text"]
            return response
        except Exception as e:
            print("Rasa Returned:", e)
            return ERROR_CODES[1]

    def __read_yaml__(self, path: str):
        with open(f"{path}", "r", encoding="utf-8") as file:
            yaml_file = yaml.safe_load(file)
            if yaml_file is None:
                raise Exception("YAML File is empty.")
            return yaml_file

    def get_similarity(self, input_sentence: str, sentence: str):
        seq = difflib.SequenceMatcher(None, input_sentence, sentence)
        d = seq.ratio() * 100
        return round(d, 2)

    def extract_entities(self, input_sentence: str):
        input_sentence = input_sentence.split()
        output_sentence = input_sentence.copy()

        entities = []

        for word in input_sentence:
            if word.__contains__("%"):
                new_word = word.replace("%", "")

                if new_word.isdigit():
                    entities.append(int(new_word))
                    output_sentence.remove(word)
                    continue

            if word.isdigit():
                output_sentence.remove(word)
                entities.append(int(word))
                continue

            for prefix in ["ein", "an", "aus"]:
                if prefix is word or word.startswith(prefix) and word not in self.wrong_words:
                    entities.append(word)

        output_sentence = " ".join(output_sentence)
        return output_sentence, entities

    def manual_text_to_commands(self, input_sentence: str):
        """
        Der Erste Schritt der mit dem User Input ausgeführt wird. Der User Input wird mit den Intents verglichen und der
        beste Intent wird zurückgegeben.
        :param input_sentence: Der blanke User Input.
        :return: Der beste Intent, die passende Antwort und die Entities.
        """
        intent_similarities = {}
        similarity = 100
        best_intent = None
        if not input_sentence:
            return

        input_sentence, entities = self.extract_entities(input_sentence)  # Entities werden extrahiert
        logger.debug('User input: "%s" - Entities: "%s"', input_sentence, entities)

        # Iteriert über alle Intents und deren [Beispiele, Entity Anzahl]
        for intent, examples in self.commands.items():
            examples = examples[0]
            entity_count = self.commands[intent][1]

            # Die Anzahl der Entities wird verglichen, um unnötige Berechnungen zu vermeiden
            if entity_count != len(entities):
                continue

            for sentence in examples:
                # Falls es ein exaktes Match gibt, wird der Intent direkt gesetzt
                if input_sentence in sentence:
                    logger.debug(f"{BLUE}Exaktes Match gefunden: {RESET}{intent}")
                    intent_similarities[intent] = 100
                    break

                similarity = self.get_similarity(input_sentence, sentence)
                if intent in intent_similarities:
                    if intent_similarities[intent] < similarity:
                        intent_similarities[intent] = similarity
                else:
                    intent_similarities[intent] = similarity

        # Wenn ein exaktes Match gefunden wurde, wird der Intent zurückgegeben
        if not best_intent:
            best_intent = max(intent_similarities, key=intent_similarities.get)
            similarity = intent_similarities[best_intent]

        logger.info(f"{BLUE}Höchste Wahrscheinlichkeit: {RESET}{best_intent}{GREEN} | {RESET}{similarity}%%")
        #logger.info(f"{intent_similarities}")

        if self.commands[best_intent][1] != len(entities):
            logger.warning("Anzahl der Entities stimmt nicht überein.")
            best_intent = "error"
            pass
        elif intent_similarities[best_intent] < 50:
            logger.warning("Kein passender Befehl gefunden.")
            logger.info(intent_similarities)
            best_intent = "error"
            pass

        response = self.manual_command_to_response(best_intent, entities)
        if response in ERROR_CODES:
            best_intent = "error"
            entities = []

        # Gibt den besten Intent zurück und eine passende zufällige Antwort
        logger.debug(f"{BLUE}Befehl: {RESET}{best_intent} | {BLUE}Antwort: {RESET}{response}")
        return best_intent, response, entities

    def manual_command_to_response(self, command: str, entities: list):

        if command == "error":
            if "utter_fallback" not in self.command_responses:
                logger.error("Domain beinhaltet keine Fallback Nachricht.")
                return ERROR_CODES[2]
            return self.command_responses["utter_fallback"]

        if command not in self.command_responses:
            logger.error(f"{RESET}Keine Antwort für Befehl {command} gefunden.")
            return ERROR_CODES[0]

        # Gibt eine zufällige Antwort zurück
        response = random.choice(self.command_responses[command])

        runs = 0
        # Läuft so lange wie es Klammern gibt, die ersetzt werden müssen
        while "{" in response:
            if not entities:
                break
            if len(entities) <= runs:
                break

            split_1 = response.split("{", 1)
            split_2 = split_1[1].split("}", 1)

            rasa_entity_name = split_2[0]
            if rasa_entity_name not in self.entity_types:
                logger.error(f"Fehler im Datensatz; Entity {rasa_entity_name} nicht in Entity_Types gefunden.")
                return ERROR_CODES[1]
            rasa_entity_type = self.entity_types[rasa_entity_name]
            print(rasa_entity_type, type(entities[runs]))
            if rasa_entity_type is not type(entities[runs]):
                logger.error(f"{RESET}Keine Antwort für Befehl {command} gefunden.")
                return ERROR_CODES[2]

            response = split_1[0] + f"{entities[runs]}" + split_2[1]
            runs += 1
        return response


# Todo: sicherung für den fall dass entities vertauscht sind
