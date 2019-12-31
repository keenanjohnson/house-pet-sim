import time
import tkinter as tk

from random import randint

import sim_vars

from housepet_gadget import MindstormsGadget

counter = None

# This function is called whenever the button is pressed
def count():
    global counter
    # Increment counter by 1
    counter.set(counter.get() + 1)


class LegoDirective():
    def __init__(self, jsn):
        self.payload = jsn


def follow_directive():
    return LegoDirective(b'{"type":"follow"}')

def stopfollow_directive():
    return LegoDirective(b'{"type":"stopfollow"}')

# Read values from the sensors at regular intervals
def poll():

    counter.set(5)

    # Schedule the poll() f

if __name__ == '__main__':
    # Create the main window
    root = tk.Tk()
    root.title("Counter")

    # Tkinter variable for holding a counter
    counter = tk.IntVar()
    counter.set(0)

    # Create widgets (note that command is set to count and not count() )
    label_counter = tk.Label(root, width=7, textvariable=counter)
    button_counter = tk.Button(root, text="Count", command=count)

    # Lay out widgets
    label_counter.pack()
    button_counter.pack()

    gadget = MindstormsGadget()
    gadget.on_connected(8)
    time.sleep(1)
    gadget.on_custom_mindstorms_gadget_control(follow_directive())

    # Schedule the poll() function to be called periodically
    root.after(500, poll)
    root.mainloop()
