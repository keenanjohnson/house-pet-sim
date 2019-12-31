from collections import OrderedDict

import sim_vars


LEDS = OrderedDict()
LEDS['red_left'] = 'led0:red:brick-status'
LEDS['red_right'] = 'led1:red:brick-status'
LEDS['green_left'] = 'led0:green:brick-status'
LEDS['green_right'] = 'led1:green:brick-status'

LED_GROUPS = OrderedDict()
LED_GROUPS['LEFT'] = ('red_left', 'green_left')
LED_GROUPS['RIGHT'] = ('red_right', 'green_right')

LED_COLORS = OrderedDict()
LED_COLORS['BLACK'] = (0, 0)
LED_COLORS['RED'] = (1, 0)
LED_COLORS['GREEN'] = (0, 1)
LED_COLORS['AMBER'] = (1, 1)
LED_COLORS['ORANGE'] = (1, 0.5)
LED_COLORS['YELLOW'] = (0.1, 1)

LED_DEFAULT_COLOR = 'GREEN'


class Leds():
    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    def __init__(self):
        self.leds = OrderedDict()
        self.led_groups = OrderedDict()
        self.led_colors = LED_COLORS

    def set_color(self, group, color, pct=1):
        """
        Sets brightness of LEDs in the given group to the values specified in
        color tuple. When percentage is specified, brightness of each LED is
        reduced proportionally.
        Example::
            my_leds = Leds()
            my_leds.set_color('LEFT', 'AMBER')
        """

        print("LED: ", group, "is", color)
        sim_vars.led_count = sim_vars.led_count + 1
