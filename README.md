# PiLN
Raspberry Pi Electric Kiln Controller

This is my first foray into Python, Git, RPi, etc

This is what I hope to accomplish:

- Create a PID controller in Python to control an electric kiln. The program takes target temperature, rate, hold time and interval seconds as inputs.
- Daemonize it
- Use MySQL to track temperature change, firing profiles, etc
- Chart the results of firing in real time with google charts
- Wrap in all in a web front end

Firing process code is almost complete and I have it pulling from and updating MySQL. Will be adding web frontend next.

Future improvements:
- Better calculation of hold time. It should start once target temperature is reached.
- Crash/loss of power recovery
- Interrupt handling to make sure relay is off
- Add LCD display and appropriate code to update display (possibly more frequently than current code)
- Overheat shutdown
