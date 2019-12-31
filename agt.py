import time

import sim_vars


class AlexaGadget():
    """
    An Alexa-connected accessory that interacts with an Amazon Echo device over Bluetooth.
    """

    def __init__(self, gadget_config_path=None):
        print("Gadget: Init")
        self.friendly_name = "alexa device"

    def send_custom_event(self, namespace, name, payload):
        """
        Sends a simulated event to alexa.
        """

    def main(self):

        while(True):
            time.sleep(1)
            print("Gadget: Tick")
