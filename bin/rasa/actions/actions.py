# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

import SendCommand
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionStop(Action):

    def name(self) -> Text: return "action_stop"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        SendCommand.send_to_server(self.name())
        return []


class VolumeUp(Action):

    def name(self) -> Text: return "action_volume_up"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        SendCommand.send_to_server(self.name())
        return []


class VolumeDown(Action):

    def name(self) -> Text: return "action_volume_down"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        SendCommand.send_to_server(self.name())
        return []


class VolumeMute(Action):
    def name(self) -> Text: return "action_volume_mute"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        SendCommand.send_to_server(self.name())
        return []


class VolumeSet(Action):
    def name(self) -> Text: return "action_volume_set"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        SendCommand.send_to_server(command=self.name(), slot1=tracker.get_slot("volume_slot"))
        return []


class VolumeGet(Action):
    def name(self) -> Text: return "action_volume_get"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        volume = SendCommand.send_to_server(command=self.name())
        print(volume)
        if not volume:
            dispatcher.utter_message(text="Mir war es leider nicht möglich die Lautstärke zu ermitteln.")
        return [SlotSet("percent_slot", int(volume))]


class DisplayBrightness(Action):

    def name(self) -> Text: return "action_display_on_off"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(tracker.get_slot("display_num_slot"), tracker.get_slot("display_on_off_slot"))
        SendCommand.send_to_server(self.name(), slot1=tracker.get_slot("display_num_slot"), slot2=tracker.get_slot("display_on_off_slot"))
        return []