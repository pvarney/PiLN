#!/usr/bin/python


#def do_it():
#        while 1:
#                print "hi "
#                time.sleep(1)
#
#with daemon.DaemonContext():
#        do_it()

import time
import logging
import daemon
import sys
import MySQLdb
import RPi.GPIO as GPIO 
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855

# Set up MySQL Connection
sqlHost = '127.0.0.1'
sqlUser = 'piln'
sqlPass = 'p!lnp@ss'
sqlDB   = 'PiLN'

# Set up logging
LogFile = time.strftime('piln_%Y%m%d%H%M.log')
logging.basicConfig(
  filename=LogFile,
  level=logging.DEBUG,
  format='%(asctime)s %(message)s'
)
 
# PID Parameters
Kp = 2.0
Ki = 1.0
Kd = 0.0

# Global Variables for PID
LastErr = 0.0
IState  = 0.0

# MAX31855 Pins/Setup
CLK = 25
CS  = 24
DO  = 18
Sensor = MAX31855.MAX31855(CLK, CS, DO)

# Pin setup for relay
GPIO.setup(4, GPIO.OUT) ## Setup GPIO Pin 7 to OUT

# Celsius to Fahrenheit
def CtoF(c):
  return c * 9.0 / 5.0 + 32.0

# PID Update
def Update ( SP, PV, IMax, IMin ):
  global LastErr, IState
  Err = SP - PV
  Pterm = Kp * Err
  Dterm = Kd * ( Err - LastErr )
  LastErr = Err
  IState  = IState + Err

#  if IState > IMax:
#    IState = IMax
#  elif IState < IMin:
#    IState = IMin

  Iterm = Ki * IState

  print " Error: ", Err
  print "IState: ", IState
  print " Pterm: ", Pterm
  print " Iterm: ", Iterm
  print " Dterm: ", Dterm
  Output = Pterm + Iterm + Dterm

  if Output > IMax:
    Output = IMax
  elif Output < IMin:
    Output = IMin

  return Output


# Loop to run each segment of the firing profile
def fire(run_id,seg,set_temp,rate,hold_min,int_sec):
  
  SetTmp  = set_temp
  Rate    = rate
  HoldSec = hold_min * 60
  IntSec  = int_sec
  RampMin = 0.0
  RampTmp = 0.0
  ReadTmp = 0.0
  StartTmp= 0.0
  TmpDif  = 0.0
  Steps   = 0.0
  StepTmp = 0.0
  StartSec= 0.0
  EndSec  = 0.0
  NextInt = 0.0
  Run     = 1
  Cnt     = 0

#  while ( ReadTmp < SetTmp ) or ( int(time.time()) <= EndSec ) or ( StartSec == 0 ):
  while Run == 1:

    if int(time.time()) >= NextInt:
      Cnt += 1
      NextInt += IntSec
  
      if RampTmp < SetTmp:
        RampTmp += StepTmp 
      elif RampTmp > SetTmp:
        RampTmp = SetTmp
  
      # Get temp
      ReadCTmp = Sensor.readTempC()
      ReadTmp = CtoF(ReadCTmp)
      ReadCITmp = Sensor.readInternalC()
      ReadITmp = CtoF(ReadCITmp)
  
      if StartTmp == 0:
        StartTmp = ReadTmp
        StartSec = int(time.time())
        NextInt  = StartSec + IntSec
        TmpDif   = SetTmp - StartTmp
        RampMin  = ( TmpDif / Rate ) * 60
        Steps    = ( RampMin * 60 ) / IntSec
        StepTmp  = TmpDif / Steps
        EndSec   = StartSec + ( RampMin * 60 ) + ( hold_min * 60 )
        RampTmp  = StartTmp + StepTmp
  
        print "    Set Temp: ", SetTmp
        print "  Start Temp: ", StartTmp
        print " Temp Change: ", TmpDif
        print "Ramp Minutes: ", RampMin
        print "       Steps: ", Steps
        print "   Step Temp: ", StepTmp
        print "    Interval: ", IntSec
        print "    StartSec: ", StartSec
        print "      EndSec: ", EndSec
  
      Output = Update(RampTmp,ReadTmp,100,0)
      CycleOnSec  = IntSec * ( Output * 0.01 )
      TimeRemain = int ( ( EndSec - int(time.time()) ) / 60 )
  
      print ("{:5d} - Temp: {:5.2f}  SetTemp: {:5.2f}  Target: {:5.2f}  Output: {:5.2f}  CycleOnSec: {:5.2f}  Remaining Minutes: {:5d}".format(Cnt,ReadTmp,RampTmp,SetTmp,Output,CycleOnSec,TimeRemain))
      print "RunID: ", run_id
      print "Segment: ", seg
  
      SQL = "INSERT INTO Firing (run_id, segment, datetime, set_temp, temp, int_temp, pid_output) VALUES ( '%d', '%d', '%s', '%.2f', '%.2f', '%.2f', '%.2f' )" % ( run_id, seg, time.strftime('%Y-%m-%d %H:%M:%S'), RampTmp, ReadTmp, ReadITmp, Output )
      try:
        sqlCur.execute(SQL)
        sqlConn.commit()
      except:
        sqlConn.rollback()
        print "DB Write failed!"
  
      print " ==> On"
      GPIO.output(4,True) ## Turn on GPIO pin 7
      time.sleep(CycleOnSec)
      print " ==> Off"
      GPIO.output(4,False) ## Turn on GPIO pin 7



logging.info("===START PiLN Firing Daemon===")
logging.info("Polling for 'Started' firing profiles...")

while 1:

  # Check for 'Started' firing profile
  sqlConn = MySQLdb.connect(sqlHost, sqlUser, sqlPass, sqlDB);
  sqlCur  = sqlConn.cursor()
  sqlCur.execute("select run_id from Profiles where state='Started'")
  data = sqlCur.fetchone()
  run_id = data[0]

  if run_id:
    logging.info("Run ID %d is active - starting firing profile" % run_id)

    StTime=time.strftime('%Y-%m-%d %H:%M:%S')
    logging.debug("Update profile %d start time to %s", run_id, StTime)
    SQL = "UPDATE Profiles SET start_time='%s' where run_id=%d" % ( StTime, run_id )
    try:
      sqlCur.execute(SQL)
      sqlConn.commit()
    except:
      sqlConn.rollback()
      logging.error("DB Update failed!")
  
    # Get segments
    logging.info("Get segments for run ID %d" % run_id)
    SQL="select * from Segments where run_id='%d'" % run_id
    sqlCur.execute(SQL)
    ProfSegs = sqlCur.fetchall()

    for Row in ProfSegs:
      run_id = Row[0]
      seg = Row[1]
      set_temp = Row[2]
      rate = Row[3]
      hold_min = Row[4]
      int_sec = Row[5]
      logging.info(
        "Run ID %d, segment %d parameters: Target Temp: %d, Rate: %d, Hold Minutes: %d, Interval Seconds: %d",
        run_id, seg, set_temp, rate, hold_min, int_sec
      )

      StTime=time.strftime('%Y-%m-%d %H:%M:%S')
      logging.debug("Update run id %d, segment %d start time to %s", run_id, seg, StTime)
      SQL = "UPDATE Segments SET start_time='%s' where run_id=%d and segment=%d" % ( StTime, run_id, seg )
      try:
        sqlCur.execute(SQL)
        sqlConn.commit()
      except:
        sqlConn.rollback()
        logging.error("DB Update failed!")
  
      fire(run_id,seg,set_temp,rate,hold_min,int_sec)

      EndTime=time.strftime('%Y-%m-%d %H:%M:%S')
      logging.debug("Update run id %d, segment %d end time to %s" % run_id, set, EndTime)
      SQL = "UPDATE Segments SET end_time='%s' where run_id=%d and segment=%d" % ( EndTime, run_id, seg )
      try:
        sqlCur.execute(SQL)
        sqlConn.commit()
      except:
        sqlConn.rollback()
        logging.error("DB Update failed!")

  sqlConn.close() 
  time.sleep(2)
