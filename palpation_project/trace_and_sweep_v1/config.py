#########    SET THESE    #########

# trace params
xspan = 60  # [mm] of total x travel
yspan = 0 # [mm] of total y travel
d = 1      # [mm] between each point
zspan = 30 # [mm] of maximum z travel (to prevent running into table)
dz = 1     # [mm] of z increment (how far it will move down on each iteration before checking if encoder_value has changed)
encoder_value_delta_threshold = 10 # [nm] amount encoder value must change to detect surface

# sweep params
n_sweep_points = 3 # number of points to perform sweep on after tracing is complete

#########    SHOULDN'T HAVE TO CHANGE THESE    #########

# for labview tcp connection
WIFI_HOST = '0.0.0.0'        # Accept connections from any IP
WIFI_PORT = 5003             # Port to receive Wi-Fi data
BUFFER_SIZE = 1024           # Size of buffer for receiving data

# for kuka tcp connection
KUKA_HOST = '172.31.1.147'   # KUKA iiwa robot IP address
KUKA_PORT = 30004           # KUKA listening port
