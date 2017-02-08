# PiLN
Raspberry Pi Kiln Controller

This is my first foray into Python, Git, RPi, etc - Please be kind ;-)

This is what I hoped to accomplish - and I think I did:

- Create a PID controller in Python to control an electric kiln. The program takes target temperature, rate, hold time and interval seconds as inputs.
- Daemonize it
- Use MySQL to track temperature change, firing profiles, etc
- Chart the results of firing in real time with google charts
- Wrap in all in a web front end

Many many many thanks to all those who post helpful tidbits out on the web - those on stackoverflow.com in particular. Way to many bits and pieces to give any particular credit, but I did use the init script from http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/ for starting up the firing daemon.

All comments, questions and suggestions welcome!

Bugs/Needs:
- Having issues getting service to start on reboot. Currently starting manually.
- Need to provide wiring diagram
- Need to provide SQL table structure

Future improvements:
- Better calculation of hold time. It should start once target temperature is reached.
- Crash/loss of power recovery
- Interrupt handling to make sure relay is off
- Add LCD display and appropriate code to update display (possibly more frequently than current code)
- Overheat shutdown

Install:
- Hardware: Raspberry Pi 3, MAX31855 thermocouple interface from Adafruit (https://www.adafruit.com/product/269), High temperature (2372 F) type K thermocouple (http://r.ebay.com/JCMymQ), 2 x 40amp Solid State Relays (http://a.co/8PtFgIr).
- Put files in /home/PiLN
- Using Python, MySQL, Apache currently versions as of February 2017.
- Required Python modules (don't remember which are part of the standard distribution): cgi, MySQLdb, jinja2, sys, re, datetime, pymysql, json, time, logging, RPi.GPIO, Adafruit_MAX31855.
- Automatic startup:

		sudo ln -s /home/PiLN/daemon/pilnfired /etc/init.d/pilnfired		
		sudo update-rc.d pilnfired defaults
		
- Apache/Web:

		sudo mkdir /var/www/html/images	
		sudo mkdir /var/www/html/style	
		sudo ln -s /home/PiLN/images/hdrback.png /var/www/html/images/hdrback.png	
		sudo ln -s /home/PiLN/images/piln.png /var/www/html/images/piln.png	
		sudo ln -s /home/PiLN/style/style.css /var/www/html/style/style.css
	
  	Added the following ScriptAlias and Directory parameters under "IfDefine ENABLE_USR_LIB_CGI_BIN" in /etc/apache2/conf-available/serve-cgi-bin.conf:
	
		ScriptAlias /pilnapp/ /home/PiLN/app/	
		  <Directory "/home/PiLN/app/">	  
		    AllowOverride None	    
		    Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch	    
		    Require all granted	    
		  </Directory>
	  
	Finally, I had to create these links to get the cgi modules enabled:
	
		cd /etc/apache2/mods-enabled
		sudo ln -s ../mods-available/cgid.conf cgid.conf
		sudo ln -s ../mods-available/cgid.load cgid.load
		sudo ln -s ../mods-available/cgi.load cgi.load
		
		



  
