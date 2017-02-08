# PiLN
Raspberry Pi Kiln Controller

This is my first foray into Python, Git, RPi, etc - Please be kind ;-)

This is what I hoped to accomplish - and did I think:

- Create a PID controller in Python to control an electric kiln. The program takes target temperature, rate, hold time and interval seconds as inputs.
- Daemonize it
- Use MySQL to track temperature change, firing profiles, etc
- Chart the results of firing in real time with google charts
- Wrap in all in a web front end

Many many many thanks to all those who post helpful tidbits out on the web - those on stackoverflow.com in particular. Way to many bits and pieces to give any particular credit, but I did use the init script from http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/ for starting up the firing daemon.

All comments, questions and suggestions welcome!

Future improvements:
- Better calculation of hold time. It should start once target temperature is reached.
- Crash/loss of power recovery
- Interrupt handling to make sure relay is off
- Add LCD display and appropriate code to update display (possibly more frequently than current code)
- Overheat shutdown

Install:
- Required Python modules (don't remember which are part of the standard distribution): cgi, MySQLdb, jinja2, sys, re, datetime, pymysql, json, time, logging, RPi.GPIO, Adafruit_MAX31855.MAX31855
- Automatic startup:
