import json
from itertools import chain, zip_longest

opening_text = [
    "Cool, ich bin schon dabei.",
    "Ich arbeite schon dran, Meister."
    "Nur einen kurzen Augenblick.",
]

paths = {
    'discord': "C:\\Users\\Hereux\\AppData\\Local\\Discord\\app-1.0.9004\\Discord.exe",
    'taschenrechner': "C:\\Windows\\System32\\calc.exe",
    "ilovemusic": "C:\\Program Files (x86)\\ILoveMusic Desktop\\ILoveMusic\\IloveMusic.exe",
    "radio": "C:\\Program Files (x86)\\ILoveMusic Desktop\\ILoveMusic\\IloveMusic.exe",
    "opera": "G:\\Users\\Marc\\AppData\\Local\\Programs\\Opera GX\\launcher.exe"
}

radios = {
    "ilovemonstercat": "monstercat",
    "ilovemonster": "monstercat",
    "monstercat": "monstercat",
    "iloveradio": "radio",
    "ilovetodance": "todance",
    "ilove2dance": "todance",
    "ilovedance": "todance",
    "ilovebass": "bass",
    "bass": "bass",
    "ilovechillhop": "chillhop",
    "ilovechill": "chillhop",
    "chillhop": "chillhop",
    "ilovedancefirst": "dancefirst",
    "dancefirst": "dancefirst",
    "ilovedancehistory": "dancehistory",
    "dancehistory": "dancehistory",
    "ilovegreatesthits": "greatesthits",
    "ilovegreatest": "greatesthits",
    "greatesthits": "greatesthits",
    "ilovehardstyle": "hardstyle",
    "hardstyle": "hardstyle",
    "ilovemainstage": "mainstage",
    "mainstage": "mainstage",
    "ilovemashup": "mashup",
    "mashup": "mashup",
    "ilovemusicandchill": "musicandchill",
    "ilovemusicchill": "musicandchill",
    "musicandchill": "musicandchill",
    "ilovepartyhard": "partyhard",
    "partyhard": "partyhard",
    "ilovedjsfrommars": "djsfrommars",
    "ilovemars": "djsfrommars",
    "djsfrommars": "djsfrommars",
    "mars": "djsfrommars",
    "ilovethedj": "thedj",
    "ilovedj": "thedj",
    "thedj": "thedj",
    "djmag": "thedj",
    "ilovedjmag": "djmag",
    "iloveworkout": "workout",
    "workout": "workout"
}


def __write_to_txt__(text: str, reset: bool = False):
    """
    Schreibt den Text in eine Textdatei.
    :param text:
    :param reset:
    :return:
    """
    if reset:
        mode = "w"
    else:
        mode = "a"

    with open("bin/command_history.txt", mode, encoding="utf-8") as file:
        file.writelines([f"{text}", "\n"])
        file.close()
    return True

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def __is_word_bool__(word: str):
    """
    Simple function to check if a word CONTAINS a boolean.
    :param word: The word to check.
    :return: True if word contains a boolean, False if not.
    """
    if word.__contains__("ein") or word.__contains__("an") or word.__contains__("aus"):
        return True
    return False


def __split_boolean__(word: str):
    """
    Simple function to split a boolean from the rest of the word.
    :param word: The word to split.
    :return: The word without the boolean, and the boolean.
    """

    rword = word
    state = None
    if __is_word_bool__(word):
        rword = word.replace("ein", "")
        rword = rword.replace("an", "")
        state = True
        if rword == word:
            rword = word.replace("aus", "")
            state = False
    return rword, state


def writetojson(filename, variable, value):
    with open(f"bin/{filename}.json", mode="r", encoding="utf-8") as read:  # Öffnet die angegebene Datei im Lesemodus
        jsonfile = json.load(read)  # Liest die Datei aus

        with open(f"bin/{filename}.json", mode="w", encoding="utf-8") as write:  # Öffnet die Datei im Schreibmodus
            jsonfile[variable] = value
            json.dump(jsonfile, write, ensure_ascii=False, indent=4)  # Speichert die abgeänderte Datei


def check_for_internet():
    import socket
    try:
        socket.create_connection(("www.google.com", 80)).close()
        return True
    except OSError:
        return False


def alternate_lists(list_a, list_b=None):
    if list_b is None:
        list_b = []

    for item in chain(*zip_longest(list_a, list_b, fillvalue=None)):
        if item is not None:
            yield item