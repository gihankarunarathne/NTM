
from subprocess import call, STDOUT 
import time
import threading
import os
from threading import Thread

class Pinger(threading.Thread):
    ### +++ ###
    def __init__(self, target = "google.com", callback = None):
        Thread.__init__(self)
        self.target = target
        self.last_speed = -1
        self.callback = callback
        
    ### +++ ###
    def run(self):
        self.run = True
        cmd = "ping -q -c1 -W 2 " + self.target
        while self.run:
            pingout = os.popen(cmd, "r")
            if pingout:
                self.last_speed = self.parse_ping_out(pingout)                      
                #print self.last_speed
                if self.callback:
                    self.callback(self, self.last_speed)
            if not self.run:
                break
            time.sleep(2)
    
    ### +++ ###
    def stop(self):
        self.run = False
        
    ### +++ ###
    def parse_ping_out(self, out_text):
        while 1:
            line = out_text.readline()
            if not line:
                return -1
            else:
                if line.startswith("rtt"):
                    i1 = line.find(" = ")
                    if i1 > 0:
                        i2 = line.find("/", i1)
                        if i2 > 0:
                            i1 += 3
                            speed = float(line[i1:i2])
                            return speed
                        else:
                            return -3
                    else:
                        return -2
    ### --- ###
### ---- ###

"""
# TEST
class Listener():
    def notify(self, caller, data):
        print "Notify: " + str(data)

listener = Listener()
        
print "Init..."
p = Pinger("google.com", listener.notify)
print "Start..."
p.start()
print "Sleep..."
time.sleep(10)
print "Stop!"
p.stop()
"""