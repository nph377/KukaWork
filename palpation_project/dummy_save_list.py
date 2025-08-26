import random
import numpy as np
import datetime
import time
import pytz

n = 5
dummy_data = []
for x in range(n):
    for y in range(n):
        z = random.randint(0,n*2)
        dummy_data.append([x,y,z])

dummy_data = np.array(dummy_data)
print(dummy_data)

epoch_time = time.time()
dt_object = datetime.datetime.fromtimestamp(epoch_time)
formatted_time = dt_object.strftime("%Y-%m-%d_%H-%M-%S")
filename = "dummy_data_" + formatted_time
np.savetxt(f"surface_data/{filename}.csv", dummy_data, delimiter=",", header="x,y,z", comments='', fmt="%.3f")