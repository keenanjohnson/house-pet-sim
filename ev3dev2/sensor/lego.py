import time
import sim_vars


class InfraredSensor():
    """
    Infrared sensor simulator
    """

    def __init__(self):
        self.mode = 'IR-Seek'

    def heading(self):
        """
        Gets the simulated heading to the beacon
        """
        return sim_vars.ir_beacon_heading


class TouchSensor():
    """
    Touch sensor simulator
    """

    def __init__(self):
        self.mode = 'IR-Seek'

    def wait_for_bump(self):
        """
        Waits for a simulated bump.
        """
        while not(sim_vars.touch_bump):
            time.sleep(0.1)
        
        return True


class ColorSensor():
    """
    Color sensor simulator
    """

    def __init__(self, address):
        self.mode = 'COL-AMBIENT'
        self.ambient_light_intensity = 0

