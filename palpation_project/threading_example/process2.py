import time

def f2(state_dict):
    print("f2 waiting")
    while state_dict["state"] != "done":
        time.sleep(.1)
    print("f2 done")


