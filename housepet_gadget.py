#!/usr/bin/env python3
# Copyright 2019 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
# 
# You may not use this file except in compliance with the terms and conditions 
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMAZON SPECIFICALLY DISCLAIMS, WITH 
# RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING 
# THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

import os
import sys
import time
import logging
import json
import random
import threading
from enum import Enum

from agt import AlexaGadget

from ev3dev2.led import Leds
from ev3dev2.motor import OUTPUT_C, OUTPUT_D, MoveTank, SpeedPercent, MoveSteering
from ev3dev2.sensor.lego import InfraredSensor
from ev3dev2.sensor.lego import TouchSensor
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sound import Sound

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import iot_api_client as iot
from iot_api_client.rest import ApiException
from iot_api_client.configuration import Configuration

# Set the logging level to INFO to see messages from AlexaGadget
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger = logging.getLogger(__name__)

oauth_client = BackendApplicationClient(client_id='FIXME')
token_url = "https://login.arduino.cc/oauth/token"

oauth = OAuth2Session(client=oauth_client)
token = oauth.fetch_token(
    token_url=token_url,
    client_id='FIXME',
    client_secret='FIXME',
    audience="https://api2.arduino.cc/iot"
)

client_config = Configuration(host="http://api2.arduino.cc/iot")
client_config.access_token = token.get("access_token")
client = iot.ApiClient(client_config)

id = 'FIXME'

api_instance = iot.PropertiesV2Api(client)

class Direction(Enum):
    """
    The list of directional commands and their variations.
    These variations correspond to the skill slot values.
    """
    FORWARD = ['forward', 'forwards', 'go forward']
    BACKWARD = ['back', 'backward', 'backwards', 'go backward']
    LEFT = ['left', 'go left']
    RIGHT = ['right', 'go right']
    STOP = ['stop', 'brake', 'halt']


class Command(Enum):
    """
    The list of preset commands and their invocation variation.
    These variations correspond to the skill slot values.
    """
    MOVE_CIRCLE = ['circle', 'move around']
    MOVE_SQUARE = ['square']
    SENTRY = ['guard', 'guard mode', 'sentry', 'sentry mode']
    PATROL = ['patrol', 'patrol mode']
    FIRE_ONE = ['cannon', '1 shot', 'one shot']
    FIRE_ALL = ['all shots', 'all shot']


class EventName(Enum):
    """
    The list of custom event name sent from this gadget
    """
    SENTRY = "Sentry"
    PROXIMITY = "Proximity"
    SPEECH = "Speech"
    POWER = "Power"


class MindstormsGadget(AlexaGadget):
    """
    A Mindstorms gadget that can perform bi-directional interaction with an Alexa skill.
    """

    def __init__(self):
        """
        Performs Alexa Gadget initialization routines and ev3dev resource allocation.
        """
        super().__init__()

        # Robot state
        self.patrol_mode = False
        self.follow_mode = False

        # Internal Variables
        self.light_intensity = 0
        self.batt_voltage = 0

        # Connect two large motors on output ports B and C
        #self.drive = MoveTank(OUTPUT_D, OUTPUT_C)
        self.steerdrive = MoveSteering(OUTPUT_C, OUTPUT_D)
        self.leds = Leds()
        self.ir = InfraredSensor()
        self.ir.mode = 'IR-SEEK'
        self.touch = TouchSensor()
        self.light = ColorSensor(address='ev3-ports:in4')
        self.sound = Sound()

        # Start threads
        threading.Thread(target=self._patrol_thread, daemon=True).start()
        threading.Thread(target=self._follow_thread, daemon=True).start()
        threading.Thread(target=self._pat_thread, daemon=True).start()
        threading.Thread(target=self._power_thread, daemon=True).start()
        threading.Thread(target=self._light_sensor_thread, daemon=True).start()

    def on_connected(self, device_addr):
        """
        Gadget connected to the paired Echo device.
        :param device_addr: the address of the device we connected to
        """
        self.leds.set_color("LEFT", "GREEN")
        self.leds.set_color("RIGHT", "GREEN")
        logger.info("{} connected to Echo device".format(self.friendly_name))

    def on_disconnected(self, device_addr):
        """
        Gadget disconnected from the paired Echo device.
        :param device_addr: the address of the device we disconnected from
        """
        self.leds.set_color("LEFT", "BLACK")
        self.leds.set_color("RIGHT", "BLACK")
        logger.info("{} disconnected from Echo device".format(self.friendly_name))

    def on_custom_mindstorms_gadget_control(self, directive):
        """
        Handles the Custom.Mindstorms.Gadget control directive.
        :param directive: the custom directive with the matching namespace and name
        """
        try:
            payload = json.loads(directive.payload.decode("utf-8"))
            print("Control payload: {}".format(payload), file=sys.stderr)
            control_type = payload["type"]
            if control_type == "move":

                # Expected params: [direction, duration, speed]
                self._move(payload["direction"], int(payload["duration"]), int(payload["speed"]))

            if control_type == "command":
                # Expected params: [command]
                self._activate(payload["command"])

            if control_type == "follow":
                self.follow_mode = True
            
            if control_type == "stopfollow":
                self.follow_mode = False

        except KeyError:
            print("Missing expected parameters: {}".format(directive), file=sys.stderr)

    def _move(self, direction, duration: int, speed: int, is_blocking=False):
        """
        Handles move commands from the directive.
        Right and left movement can under or over turn depending on the surface type.
        :param direction: the move direction
        :param duration: the duration in seconds
        :param speed: the speed percentage as an integer
        :param is_blocking: if set, motor run until duration expired before accepting another command
        """
        print("Move command: ({}, {}, {}, {})".format(direction, speed, duration, is_blocking), file=sys.stderr)
        if direction in Direction.FORWARD.value:
            self.drive.on_for_seconds(SpeedPercent(speed), SpeedPercent(speed), duration, block=is_blocking)

        if direction in Direction.BACKWARD.value:
            self.drive.on_for_seconds(SpeedPercent(-speed), SpeedPercent(-speed), duration, block=is_blocking)

        if direction in (Direction.RIGHT.value + Direction.LEFT.value):
            self._turn(direction, speed)
            self.drive.on_for_seconds(SpeedPercent(speed), SpeedPercent(speed), duration, block=is_blocking)

        if direction in Direction.STOP.value:
            self.drive.off()
            self.patrol_mode = False

    def _activate(self, command, speed=50):
        """
        Handles preset commands.
        :param command: the preset command
        :param speed: the speed if applicable
        """
        print("Activate command: ({}, {})".format(command, speed), file=sys.stderr)
        if command in Command.MOVE_CIRCLE.value:
            self.drive.on_for_seconds(SpeedPercent(int(speed)), SpeedPercent(5), 12)

        if command in Command.MOVE_SQUARE.value:
            for i in range(4):
                self._move("right", 2, speed, is_blocking=True)

        if command in Command.PATROL.value:
            # Set patrol mode to resume patrol thread processing
            self.patrol_mode = True

        if command in Command.SENTRY.value:
            self.sentry_mode = True
            self._send_event(EventName.SPEECH, {'speechOut': "Sentry mode activated"})

            # Perform Shuffle posture
            self.drive.on_for_seconds(SpeedPercent(80), SpeedPercent(-80), 0.2)
            time.sleep(0.3)
            self.drive.on_for_seconds(SpeedPercent(-40), SpeedPercent(40), 0.2)

            self.leds.set_color("LEFT", "YELLOW", 1)
            self.leds.set_color("RIGHT", "YELLOW", 1)

    def _turn(self, direction, speed):
        """
        Turns based on the specified direction and speed.
        Calibrated for hard smooth surface.
        :param direction: the turn direction
        :param speed: the turn speed
        """
        if direction in Direction.LEFT.value:
            self.drive.on_for_seconds(SpeedPercent(0), SpeedPercent(speed), 2)

        if direction in Direction.RIGHT.value:
            self.drive.on_for_seconds(SpeedPercent(speed), SpeedPercent(0), 2)

    def _send_event(self, name: EventName, payload):
        """
        Sends a custom event to trigger a sentry action.
        :param name: the name of the custom event
        :param payload: the sentry JSON payload
        """
        self.send_custom_event('Custom.Mindstorms.Gadget', name.value, payload)

    def _patrol_thread(self):
        """
        Performs random movement when patrol mode is activated.
        """
        while True:
            while self.patrol_mode:
                print("Patrol mode activated randomly picks a path", file=sys.stderr)
                direction = random.choice(list(Direction))
                duration = random.randint(1, 5)
                speed = random.randint(1, 4) * 25

                while direction == Direction.STOP:
                    direction = random.choice(list(Direction))

                # direction: all except stop, duration: 1-5s, speed: 25, 50, 75, 100
                self._move(direction.value[0], duration, speed)
                time.sleep(duration)
            time.sleep(1)

    def _pat_thread(self):
        """
        Detects when the touch sensor is pressed.
        """
        while True:
            self.touch.wait_for_bump()
            sound = "Ahh, I like that."
            self._send_event(EventName.SPEECH, {'speechOut': sound})

    def _light_sensor_thread(self):
        """
        """
        while True:
            self.light.mode='COL-AMBIENT'
            time.sleep(0.5)
            self.light_intensity = self.light.ambient_light_intensity
            if self.batt_voltage < 3.6:
                # Set the LED to be red.
                self.light.mode='REF-RAW'
            else:
                self.light.mode='COL-COLOR'
                # Set the LED to be white.

            print("Light Intensity: ", self.light_intensity)

            time.sleep(5)

    def _follow_thread(self):
        """
        The thread to manage following the lease.
        """
        while True:
            if self.follow_mode:
                # Get heading to beacon
                heading = self.ir.heading()
                print("IR Heading: ", heading)

                # Can't see the beacon
                if heading == 0:
                    time.sleep(1)
                    continue

                drive_dir = -heading

                # Drive
                self.steerdrive.on_for_rotations(drive_dir, SpeedPercent(30), 2, block=True)

            time.sleep(1)


    def _power_thread(self):
        """
        Sends power output to Alexa skill.
        """

        charge_current_pid = 'FIXME'
        load_current_pid = 'FIXME'
        batt_voltage_pid = 'FIXME'
        
        time.sleep(2)

        while True:
            try:
                # list properties_v2
                api_response = api_instance.properties_v2_show(id, batt_voltage_pid)
                print('Battery Voltage: ', round(api_response.last_value, 3))
                voltage = round(api_response.last_value, 3)
                voltage = 3.54
                self.batt_voltage = voltage
            except ApiException as e:
                print("Exception when calling PropertiesV2Api->propertiesV2List: %s\n" % e)

            try:
                api_response = api_instance.properties_v2_show(id, load_current_pid)
                print('Load Current: ', round(api_response.last_value, 2))
                load_current = round(api_response.last_value, 1)
            except ApiException as e:
                print("Exception when calling PropertiesV2Api->propertiesV2List: %s\n" % e)

            try:
                api_response = api_instance.properties_v2_show(id, charge_current_pid)
                print('Charge Current: ', round(api_response.last_value, 2))
                charge_current = round(api_response.last_value, 1)
            except ApiException as e:
                print("Exception when calling PropertiesV2Api->propertiesV2List: %s\n" % e)

            time.sleep(15)

            self._send_event(EventName.POWER, {'voltage': voltage, 'load_current': load_current, 'charge_current': charge_current, 'light':self.light_intensity })
            


if __name__ == '__main__':

    gadget = MindstormsGadget()

    # Set LCD font and turn off blinking LEDs
    os.system('setfont Lat7-Terminus12x6')
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")

    # Startup sequence
    gadget.sound.play_song((('C4', 'e'), ('D4', 'e'), ('E5', 'q')))
    gadget.leds.set_color("LEFT", "GREEN")
    gadget.leds.set_color("RIGHT", "GREEN")

    # Gadget main entry point
    gadget.main()

    # Shutdown sequence
    gadget.sound.play_song((('E5', 'e'), ('C4', 'e')))
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")