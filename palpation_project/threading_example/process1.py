import time

def f1(state_dict):
    for i in range(3):
        print(f"f1: {i}")
        time.sleep(1)
    state_dict["state"] = "done"
