#!/usr/bin/python


#def do_it():
#        while 1:
#                print "hi "
#                time.sleep(1)
#
#with daemon.DaemonContext():
#        do_it()

import time
import logging as L
import daemon
import sys
import MySQLdb
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855

# Set up MySQL Connection
SQLHost = '127.0.0.1'
SQLUser = 'piln'
SQLPass = 'p!lnp@ss'
SQLDB   = 'PiLN'

# Set up logging
LogFile = time.strftime('log/piln_%Y%m%d.log')
L.basicConfig(
  filename=LogFile,
  level=L.DEBUG,
  format='%(asctime)s %(message)s'
)

# PID Parameters
Kp = 2.0
Ki = 1.0
Kd = 0.0

# Global Variables for PID
LastErr  = 0.0
Integral = 0.0

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
def Update ( SetPoint, ProcValue, IMax, IMin, WindowMSec ):

  L.debug(
    "Entering PID update with parameters SetPoint:%0.2f, ProcValue:%0.2f, IMax:%0.2f, IMin:%0.2f, WindowMSec:%d" %
    ( SetPoint, ProcValue, IMax, IMin, WindowMSec )
  )

  global LastErr, Integral

  Err      = SetPoint - ProcValue

  Pterm    = Kp * Err

  Dterm    = Kd * ( Err - LastErr )
  LastErr  = Err

  Integral+= Err
  if Integral > IMax:
    Integral = IMax
  elif Integral < IMin:
    Integral = IMin
  Iterm = Ki * Integral

  Output = Pterm + Iterm + Dterm

  if Output > 100:
    Output = 100
  elif Output < 0:
    Output = 0

  L.debug(
    "Exiting PID update with parameters Error:%0.2f, Integral:%0.2f, Pterm:%0.2f, Iterm:%0.2f, Dterm:%0.2f, Output:%0.2f" %
    ( Err, Integral, Pterm, Iterm, Dterm, Output )
  )
  return Output


# Loop to run each segment of the firing profile
def Fire(RunID,Seg,SetTmp,Rate,HoldMin,Window):

  L.debug(
    "Entering Fire function with parameters RunID:%d, Seg:%d, SetTmp:%d, Rate:%d, HoldMin:%d, Window:%d" %
    ( RunID, Seg, SetTmp, Rate, HoldMin, Window )
  )

#  global LastErr, Integral

  HoldSec  = HoldMin * 60
  RampMin  = 0.0
  RampTmp  = 0.0
  ReadTmp  = 0.0
  StartTmp = 0.0
  TmpDif   = 0.0
  Steps    = 0.0
  StepTmp  = 0.0
  StartSec = 0.0
  EndSec   = 0.0
  NextSec  = 0.0
  RunState = 1
  Cnt      = 0
#  Integral = 0.0
#  LastErr  = 0.0
  
#  while ( ReadTmp > SetTmp ) or ( time.time() <= EndSec ) or ( StartSec == 0 ):
  while RunState > 0:

    if time.time() >= NextSec:
      Cnt += 1
      NextSec += Window

#      if RampTmp > SetTmp:
      RampTmp += StepTmp

      if ( ( TmpDif < 0 ) and ( RampTmp < SetTmp ) ) or ( ( TmpDif > 0 ) and ( RampTmp >= SetTmp ) ):
          RampTmp = SetTmp
          RunState = 3

      # Get temp
      ReadCTmp  = Sensor.readTempC()
      ReadTmp   = CtoF(ReadCTmp)
      ReadCITmp = Sensor.readInternalC()
      ReadITmp  = CtoF(ReadCITmp)

      if StartTmp == 0:
        StartTmp = ReadTmp
        StartSec = time.time()
        NextSec  = StartSec + Window
        TmpDif   = SetTmp - StartTmp
        RampMin  = ( abs (TmpDif) / Rate ) * 60
        Steps    = ( RampMin * 60 ) / Window
        StepTmp  = TmpDif / Steps
        EndSec   = StartSec + ( RampMin * 60 ) + ( HoldMin * 60 )
        RampTmp  = StartTmp + StepTmp

        if TmpDif < 0:
          RunState = 2

        L.debug(
          "First pass of firing loop - SetTmp:%0.2f, StartTmp:%0.2f, TmpDif:%0.2f, RampMin:%0.2f, Steps:%d, StepTmp:%0.2f, Window:%d, StartSec:%d, EndSec:%d" %
          ( SetTmp, StartTmp, TmpDif, RampMin, Steps, StepTmp, Window, StartSec, EndSec ) 
        )
    
      Output = Update(RampTmp,ReadTmp,5000,-5000,Window)
      CycleOnSec  = Window * ( Output * 0.01 )
      RemainSec = EndSec - int ( time.time() ) 
      RemMin, RemSec = divmod(RemainSec, 60)
      RemHr, RemMin  = divmod(RemMin, 60)
      RemainTime = "%d:%02d:%02d" % (RemHr, RemMin, RemSec)
      L.debug(
        "RunID %d, Segment %d (loop %d) - RunState:%d, ReadTmp:%0.2f, RampTmp:%0.2f, SetTmp:%0.2f, Output:%0.2f, CycleOnSec:%0.2f, RemainTime:%s" %
        ( RunID, Seg, Cnt, RunState, ReadTmp, RampTmp, SetTmp, Output, CycleOnSec, RemainTime )
      )

      L.debug("Writing stats to Firing DB table...")
      SQL = "INSERT INTO Firing (run_id, segment, datetime, set_temp, temp, int_temp, pid_output) VALUES ( '%d', '%d', '%s', '%.2f', '%.2f', '%.2f', '%.2f' )" % ( RunID, Seg, time.strftime('%Y-%m-%d %H:%M:%S'), RampTmp, ReadTmp, ReadITmp, Output )
      try:
        SQLCur.execute(SQL)
        SQLConn.commit()
      except:
        SQLConn.rollback()
        L.error("DB Update failed!")

      L.debug("==>Relay On")
      GPIO.output(4,True) ## Turn on GPIO pin 7
      time.sleep(CycleOnSec)
      L.debug("==>Relay Off")
      GPIO.output(4,False) ## Turn on GPIO pin 7

    if time.time() > EndSec:
      RunState = 0


L.info("===START PiLN Firing Daemon===")
L.info("Polling for 'Started' firing profiles...")

while 1:

  # Check for 'Started' firing profile
  SQLConn = MySQLdb.connect(SQLHost, SQLUser, SQLPass, SQLDB);
  SQLCur  = SQLConn.cursor()
  RowsCnt = SQLCur.execute("select run_id from Profiles where state='Started'")
#  Data = SQLCur.fetchone()
#  RunID = Data[0]

  if RowsCnt > 0:
    Data = SQLCur.fetchone()
    RunID = Data[0]
    L.info("Run ID %d is active - starting firing profile" % RunID)

    StTime=time.strftime('%Y-%m-%d %H:%M:%S')
    L.debug("Update profile %d start time to %s" % ( RunID, StTime ) )
    SQL = "UPDATE Profiles SET start_time='%s' where run_id=%d" % ( StTime, RunID )
    try:
      SQLCur.execute(SQL)
      SQLConn.commit()
    except:
      SQLConn.rollback()
      L.error("DB Update failed!")

    # Get segments
    L.info("Get segments for run ID %d" % RunID)
    SQL="select * from Segments where run_id='%d'" % RunID
    SQLCur.execute(SQL)
    ProfSegs = SQLCur.fetchall()

    for Row in ProfSegs:
      RunID = Row[0]
      Seg = Row[1]
      SetTmp = Row[2]
      Rate = Row[3]
      HoldMin = Row[4]
      Window = Row[5]
      L.info(
        "Run ID %d, segment %d parameters: Target Temp: %0.2f, Rate: %0.2f, Hold Minutes: %d, Window Seconds: %d" %
        ( RunID, Seg, SetTmp, Rate, HoldMin, Window )
      )

      StTime=time.strftime('%Y-%m-%d %H:%M:%S')
      L.debug("Update run id %d, segment %d start time to %s" % ( RunID, Seg, StTime ) )
      SQL = "UPDATE Segments SET start_time='%s' where run_id=%d and segment=%d" % ( StTime, RunID, Seg )
      try:
        SQLCur.execute(SQL)
        SQLConn.commit()
      except:
        SQLConn.rollback()
        L.error("DB Update failed!")

      Fire(RunID,Seg,SetTmp,Rate,HoldMin,Window)

      EndTime=time.strftime('%Y-%m-%d %H:%M:%S')
      L.debug("Update run id %d, segment %d end time to %s" % ( RunID, Seg, EndTime ) )
      SQL = "UPDATE Segments SET end_time='%s' where run_id=%d and segment=%d" % ( EndTime, RunID, Seg )
      try:
        SQLCur.execute(SQL)
        SQLConn.commit()
      except:
        SQLConn.rollback()
        L.error("DB Update failed!")

    EndTime=time.strftime('%Y-%m-%d %H:%M:%S')
    L.debug("Update profile end time to %s and state to 'Completed' for run id %d" % ( EndTime, RunID ) )
    SQL = "UPDATE Profiles SET end_time='%s', state='Completed' where run_id=%d" % ( EndTime, RunID )
    try:
      SQLCur.execute(SQL)
      SQLConn.commit()
    except:
      SQLConn.rollback()
      L.error("DB Update failed!")

    L.info("Polling for 'Started' firing profiles...")


  SQLConn.close()
  time.sleep(2)
