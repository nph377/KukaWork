import numpy as np
import time

print(np.sign(-323))
print(np.sign(323))

a = [[x, x, x] for x in range(81)]
a = np.array(a)

n_points = 10

i_points = [int(i*(len(a)-1)/(n_points-1)) for i in range(n_points)]

print(i_points)
for i in i_points:
    x,y,z = a[i]
    print(i, x,y,z)

while True:
    print("hi")
    time.sleep(1)