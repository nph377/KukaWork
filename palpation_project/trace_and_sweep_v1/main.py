from threading import Thread
import time
import datetime
import numpy as np

from kuka import Kuka
from labview import LabviewTCP
from global_state import GlobalState


print("are you on the laptop hotspot?")
print("is the kuka program running?")
input("press enter to continue")

g_state = GlobalState()
kuka = Kuka(g_state)
labview = LabviewTCP(g_state)

kuka_trace = Thread(target=kuka.trace)
kuka_sweep = Thread(target=kuka.sweep)
receive_labview_data = Thread(target=labview.receive_data)

if __name__ == "__main__":

    input("press enter to begin trace")
    try:
        receive_labview_data.start()

        print("beginning trace")
        kuka_trace.start()

        while g_state.kuka_state != "trace done":
            time.sleep(1)

        input("press Enter to continue to sweep")

        print("beginning sweep")
        kuka_sweep.start()

        try:
            while g_state.kuka_state != "sweep done":
                time.sleep(1)
        finally:
            pass
    except Exception as e:
        print("Exception:")
        print(e)
    finally:
        kuka.disconnect()
        g_state.end_labview_connection = True
