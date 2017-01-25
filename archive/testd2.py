#!/usr/bin/python

import daemon
import time

#print daemon.__file__

def do_it():
	while 1:
		print "hi "
		time.sleep(1)

with daemon.DaemonContext():
	do_it()

