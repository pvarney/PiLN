# PiLN
Web-based Raspberry Pi Kiln Control Application

This is my first foray into Python, Git, RPi, etc - Please be kind ;-)

I have a good size 220v 45amp electric kiln that has the old "kiln-sitter" style temperature control with bi-metal on/off cycle adjustment knobs. I wanted something with much more precise temperature control for more consistent results and in order to do more work with glass. I started this project with an Arduino board but found the wifi connectivity and coding much too complicated. Being rather proficient in Perl, it seemed the RPi was a better solution. I wrote the original PID control in Perl, but then ported to Python since there seemed to be much more support for it on the RPi and since it was something I wanted to learn anyway.

WARNING! Electricity and heat are dangerous! Please be careful and seek professional help if you are not experienced dealing with high voltage and heat. Use this code/information at your own risk.

This is what I hoped to accomplish - and I think I did:

- Create a PID controller in Python to control an electric kiln. The program takes target temperature, rate, hold time and interval seconds as inputs.
- Daemonize it
- Use MySQL to track temperature change, firing profiles, etc
- Chart the results of firing in real time with google charts
- Wrap in all in a web front end

Many many many thanks to all those who post helpful tidbits out on the web - those on stackoverflow.com in particular. Way to many bits and pieces to give any particular credit, but I did use the init script from http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/ for starting up the firing daemon.

All comments, questions, contributions and suggestions welcome!

Bugs/Needs:
- Having issues getting service to start on reboot. Currently starting manually.
- Need to provide wiring diagram

Future improvements:
- Better calculation of hold time. It should start once target temperature is reached.
- Crash/loss of power recovery
- Interrupt handling to make sure relay is off
- Add LCD display and appropriate code to update display (possibly more frequently than current code)
- Overheat shutdown

Install:
- Hardware: Raspberry Pi 3, MAX31855 thermocouple interface from Adafruit (https://www.adafruit.com/product/269), High temperature (2372 F) type K thermocouple (http://r.ebay.com/JCMymQ), 2 x 40amp Solid State Relays (http://a.co/8PtFgIr).
- Install files in /home:
	cd /home
	sudo git clone https://github.com/pvarney/PiLN
- Using Python, MySQL, Apache currently versions as of July 2017:
	sudo apt-get install mysql-server
	sudo apt-get install mysql-client php5-mysql
	sudo apt-get install phpmyadmin
	Edit /etc/apache2/apache2.conf and add "Include /etc/phpmyadmin/apache.conf"
	sudo /etc/init.d/apache2 restart
- Use PiLN.sql to build MySQL table structures (I used phpmyadmin, but it's not required)
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
		
		



  
