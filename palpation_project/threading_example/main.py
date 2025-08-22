import threading
from process1 import f1
from process2 import f2

state_dict = {"state": None}


t1 = threading.Thread(target=f1, args=(state_dict,))
t2 = threading.Thread(target=f2, args=(state_dict,))
t1.start()
t2.start()
t1.join()
t2.join()
