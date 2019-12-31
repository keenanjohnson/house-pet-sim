import sim_vars

OUTPUT_A = 'ev3-ports:outA'
OUTPUT_B = 'ev3-ports:outB'
OUTPUT_C = 'ev3-ports:outC'
OUTPUT_D = 'ev3-ports:outD'


class SpeedValue(object):
    """
    A base class for other unit types. Don't use this directly; instead, see
    :class:`SpeedPercent`, :class:`SpeedRPS`, :class:`SpeedRPM`,
    :class:`SpeedDPS`, and :class:`SpeedDPM`.
    """

    def __eq__(self, other):
        return self.to_native_units() == other.to_native_units()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.to_native_units() < other.to_native_units()

    def __le__(self, other):
        return self.to_native_units() <= other.to_native_units()

    def __gt__(self, other):
        return self.to_native_units() > other.to_native_units()

    def __ge__(self, other):
        return self.to_native_units() >= other.to_native_units()

    def __rmul__(self, other):
        return self.__mul__(other)


class SpeedPercent(SpeedValue):
    """
    Speed as a percentage of the motor's maximum rated speed.
    """

    def __init__(self, percent):
        assert -100 <= percent <= 100,\
            "{} is an invalid percentage, must be between -100 and 100 (inclusive)".format(percent)

        self.percent = percent

    def __str__(self):
        return str(self.percent) + "%"

    def __mul__(self, other):
        assert isinstance(other, (float, int)), "{} can only be multiplied by an int or float".format(self)
        return SpeedPercent(self.percent * other)

    def to_native_units(self, motor):
        """
        Return this SpeedPercent in native motor units
        """
        return self.percent / 100 * motor.max_speed


class MoveTank():
    """
    MoveTank Class
    """

    def __init__(self):
        """
        A temp class.
        """

class MoveSteering():
    """
    MoveSteering Class
    """

    def __init__(self, left_motor_port, right_motor_port,):
        """
        Move steering class.
        """

    def on_for_rotations(self, steering, speed, rotations, brake=True, block=True):
        """
        Turns the tank treads on for a few rotations.
        """