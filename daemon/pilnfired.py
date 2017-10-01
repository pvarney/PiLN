#!/usr/bin/env python


import time
import logging as L
import sys
import MySQLdb
import RPi.GPIO as GPIO
import Adafruit_MAX31855.MAX31855 as MAX31855

# Set up MySQL Connection
SQLHost = '127.0.0.1'
SQLUser = 'piln'
SQLPass = 'p!lnp@ss'
SQLDB   = 'PiLN'
AppDir  = '/home/PiLN'

#Status File
StatFile = '/var/www/html/pilnstat.json'

# Set up logging
LogFile = time.strftime( AppDir + '/log/pilnfired.log' )
L.basicConfig(
  filename=LogFile,
  level=L.INFO,
  format='%(asctime)s %(message)s'
)

# Global Variables
#LastErr  = 0.0
#Integral = 0.0
ITerm = 0.0
LastProcVal = 0.0
SegCompStat = 0

# MAX31855 Pins/Setup
CLK = 25
CS  = 24
DO  = 18
Sensor = MAX31855.MAX31855(CLK, CS, DO)

# Pin setup for relay
GPIO.setup(4, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
GPIO.output(4,False) ## Turn off GPIO pin 7

# Celsius to Fahrenheit
def CtoF(c):
  return c * 9.0 / 5.0 + 32.0

  
# PID Update
def Update ( SetPoint, ProcValue, IMax, IMin, Window, Kp, Ki, Kd ):

  L.debug( "Entering PID update with parameters SetPoint:%0.2f, ProcValue:%0.2f, IMax:%0.2f, IMin:%0.2f," %
    ( SetPoint, ProcValue, IMax, IMin ))
  L.debug( "  Window:%d, Kp: %0.3f, Ki: %0.3f, Kd: %0.3f" %
    ( Window, Kp, Ki, Kd ))

  global ITerm, LastProcVal

  Err = SetPoint - ProcValue
  ITerm+= (Ki * Err);

  if ITerm > IMax:
    ITerm = IMax
  elif ITerm < IMin:
    ITerm = IMin

  DInput = ProcValue - LastProcVal

  #Compute PID Output
  Output = Kp * Err + ITerm - Kd * DInput;
  if Output > IMax:
    Output = IMax
  elif Output < IMin:
    Output = IMin

  #Remember for next time
  LastProcVal = ProcValue


  L.debug(
    "Exiting PID update with parameters Error:%0.2f, ITerm:%0.2f, DInput:%0.2f, Output:%0.2f" %
    ( Err, ITerm, DInput, Output )
  )

  return Output



#  global LastErr, Integral
#
#  Err      = SetPoint - ProcValue
#
#  Pterm    = Kp * Err
#
#  Dterm    = Kd * ( Err - LastErr )
#  LastErr  = Err
#
#  Integral+= Err
#  if Integral > IMax:
#    Integral = IMax
#  elif Integral < IMin:
#    Integral = IMin
#  Iterm = Ki * Integral
#
#  Output = Pterm + Iterm + Dterm
#
#  L.debug(
#    "Exiting PID update with parameters Error:%0.2f, Integral:%0.2f, Pterm:%0.2f, Iterm:%0.2f, Dterm:%0.2f, Output:%0.2f" %
#    ( Err, Integral, Pterm, Iterm, Dterm, Output )
#  )
#
#  if Output > 100:
#    Output = 100
#  elif Output < 0:
#    Output = 0
#  if Output < 0:
#    Output = 0
#
#  return Output


# Loop to run each segment of the firing profile
def Fire(RunID,Seg,TargetTmp,Rate,HoldMin,Window,Kp,Ki,Kd):

  L.info( "Entering Fire function with parameters RunID:%d, Seg:%d, TargetTmp:%d, Rate:%d," % ( RunID, Seg, TargetTmp, Rate ))
  L.info( "  HoldMin:%d, Window:%d" % ( HoldMin, Window ))

  global SegCompStat

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
  RunState = "Ramp"
  Cnt      = 0
  RampTrg  = 0
  ReadTrg  = 0
  
  while RunState != "Stopped" and RunState != "Complete":

    if time.time() >= NextSec:
      Cnt += 1
      NextSec = time.time() + Window

      # Get temp
      ReadCTmp  = Sensor.readTempC()
      ReadTmp   = CtoF(ReadCTmp)
      ReadCITmp = Sensor.readInternalC()
      ReadITmp  = CtoF(ReadCITmp)

      if RampTrg == 0:
        RampTmp += StepTmp

      if TmpDif > 0:

        # Ramp temp reached target
        if RampTmp >= TargetTmp and RampTrg == 0:
          RampTmp = TargetTmp
          RampTrg = 1
          if ReadTrg == 1:
            RunState = "Ramp complete/target temp reached"
          else:
            RunState = "Ramp complete"

        # Read temp reached target
        if ( ( TargetTmp - ReadTmp <= TargetTmp * 0.006 ) or ( ReadTmp >= TargetTmp ) ) and ReadTrg == 0:
          ReadTrg = 1
          EndSec = int(time.time()) + ( HoldMin * 60 )
          L.info( "Set temp reached - End seconds set to %d" % EndSec )
          if RampTrg == 1:
            RunState = "Ramp complete/target temp reached"
          else:
            RunState = "Target temp reached"

      elif TmpDif < 0:

        # Ramp temp reached target
        if RampTmp <= TargetTmp and RampTrg == 0:
          RampTmp = TargetTmp
          RampTrg = 1
          if ReadTrg == 1:
            RunState = "Ramp complete/target temp reached"
          else:
            RunState = "Ramp complete"

        # Read temp reached target
        if ( ( ReadTmp - TargetTmp <= TargetTmp * 0.006 ) or ( ReadTmp <= TargetTmp ) ) and ReadTrg == 0:
          ReadTrg = 1
          EndSec = int(time.time()) + ( HoldMin * 60 )
          L.info( "Set temp reached - End seconds set to %d" % EndSec )
          if RampTrg == 1:
            RunState = "Ramp complete/target temp reached"
          else:
            RunState = "Target temp reached"

      if StartTmp == 0:
        StartTmp = ReadTmp
        StartSec = int(time.time())
        NextSec  = StartSec + Window
        TmpDif   = TargetTmp - StartTmp
        RampMin  = ( abs (TmpDif) / Rate ) * 60
        Steps    = ( RampMin * 60 ) / Window
        StepTmp  = TmpDif / Steps
        EndSec   = StartSec + ( RampMin * 60 ) + ( HoldMin * 60 )
        RampTmp = StartTmp + StepTmp
        if ( TmpDif > 0 and RampTmp > TargetTmp ) or ( TmpDif < 0 and RampTmp < TargetTmp ):
          RampTmp = TargetTmp
        LastErr  = 0.0
        Integral = 0.0

#        if TmpDif < 0:
#          RunState = 2

        L.info( "First pass of firing loop - TargetTmp:%0.2f, StartTmp:%0.2f, RampTmp:%0.2f, TmpDif:%0.2f," %
          ( TargetTmp, StartTmp, RampTmp, TmpDif ))
        L.info( "  RampMin:%0.2f, Steps:%d, StepTmp:%0.2f, Window:%d, StartSec:%d, EndSec:%d" %
          ( RampMin, Steps, StepTmp, Window, StartSec, EndSec ) )
    
      #Output = Update(RampTmp,ReadTmp,50000,-50000,Window,Kp,Ki,Kd)
      Output = Update(RampTmp,ReadTmp,100,0,Window,Kp,Ki,Kd)

      CycleOnSec  = Window * ( Output * 0.01 )
      if CycleOnSec > Window:
        CycleOnSec = Window

      RemainSec = EndSec - int ( time.time() ) 
      RemMin, RemSec = divmod(RemainSec, 60)
      RemHr, RemMin  = divmod(RemMin, 60)
      RemainTime = "%d:%02d:%02d" % (RemHr, RemMin, RemSec)
      L.debug( "RunID %d, Segment %d (loop %d) - RunState:%s," % ( RunID, Seg, Cnt, RunState ))
      L.debug( "  ReadTmp:%0.2f, RampTmp:%0.2f, TargetTmp:%0.2f, Output:%0.2f, CycleOnSec:%0.2f, RemainTime:%s" %
        ( ReadTmp, RampTmp, TargetTmp, Output, CycleOnSec, RemainTime )
      )

      if Output > 0:
        L.debug("==>Relay On")
        GPIO.output(4,True) ## Turn on GPIO pin 7
        time.sleep(CycleOnSec)

      if Output < 100:
        L.debug("==>Relay Off")
        GPIO.output(4,False) ## Turn off GPIO pin 7

      # Write statu to file for reporting on web page
      sfile = open(StatFile,"w+")
      sfile.write('{\n' +
        '  "proc_update_utime": "' + str(int(time.time())) + '",\n' +
        '  "readtemp": "'          + str(int(ReadTmp))     + '",\n' +
        '  "run_profile": "'       + str(RunID)            + '",\n' +
        '  "run_segment": "'       + str(Seg)              + '",\n' +
        '  "ramptemp": "'          + str(int(RampTmp))     + '",\n' +
        '  "targettemp": "'        + str(int(TargetTmp))   + '",\n' +
        '  "segtime": "'           + str(int(RemainTime))  + '"\n' +
        '}\n'
      )
      sfile.close()

      L.debug("Writing stats to Firing DB table...")
      SQL = "INSERT INTO Firing (run_id, segment, datetime, set_temp, temp, int_temp, pid_output) VALUES ( '%d', '%d', '%s', '%.2f', '%.2f', '%.2f', '%.2f' )" % ( RunID, Seg, time.strftime('%Y-%m-%d %H:%M:%S'), RampTmp, ReadTmp, ReadITmp, Output )
      try:
        SQLCur.execute(SQL)
        SQLConn.commit()
      except:
        SQLConn.rollback()
        L.error("DB Update failed!")


      # Check if profile is still in running state
      RowsCnt = SQLCur.execute("select * from Profiles where state='Running' and run_id=%d" % RunID)

      if RowsCnt == 0:
        L.warn("Profile no longer in running state - exiting firing")
        SegCompStat = 1 
        RunState = "Stopped"
  
      if time.time() > EndSec and ReadTrg == 1:
        RunState = "Complete"
  
#      L.debug(
#            "RunState:%s, TargetTmp:%0.2f, StartTmp:%0.2f, RampTmp:%0.2f, TmpDif:%0.2f, RampMin:%0.2f, Steps:%d, StepTmp:%0.2f, Window:%d, StartSec:%d, EndSec:%d" %
#            ( RunState, TargetTmp, StartTmp, RampTmp, TmpDif, RampMin, Steps, StepTmp, Window, StartSec, EndSec ) 
#          )



L.info("===START PiLN Firing Daemon===")
L.info("Polling for 'Running' firing profiles...")

while 1:

  # Get temp
  ReadCTmp  = Sensor.readTempC()
  ReadTmp   = CtoF(ReadCTmp)
  ReadCITmp = Sensor.readInternalC()
  ReadITmp  = CtoF(ReadCITmp)

  # Write statu to file for reporting on web page
  sfile = open(StatFile,"w+")
  sfile.write('{\n' +
    '  "proc_update_utime": "' + str(int(time.time())) + '",\n' +
    '  "readtemp": "'          + str(int(ReadTmp))     + '",\n' +
    '  "run_profile": "none",\n' +
    '  "run_segment": "n/a",\n' +
    '  "ramptemp": "n/a",\n' +
    '  "targettemp": "n/a"\n' +
    '}\n'
  )
  sfile.close()

#{
#  "proc_update_utime": "1506396470",
#  "readtemp": "145",
#  "run_profile": "none",
#  "run_segment": "n/a",
#  "targettemp": "n/a"
#}


  # Check for 'Running' firing profile
  SQLConn = MySQLdb.connect(SQLHost, SQLUser, SQLPass, SQLDB);
  SQLCur  = SQLConn.cursor()
  RowsCnt = SQLCur.execute("select * from Profiles where state='Running'")

  if RowsCnt > 0:
    Data = SQLCur.fetchone()
    RunID = Data[0]
    Kp = float(Data[3])
    Ki = float(Data[4])
    Kd = float(Data[5])
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
    SQL="select * from Segments where run_id=%d" % RunID
    SQLCur.execute(SQL)
    ProfSegs = SQLCur.fetchall()

    for Row in ProfSegs:
      RunID = Row[0]
      Seg = Row[1]
      TargetTmp = Row[2]
      Rate = Row[3]
      HoldMin = Row[4]
      Window = Row[5]

      if SegCompStat == 1:
        L.debug("Profile stopped - skipping segment %d" % Seg)

      else:
        L.info( "Run ID %d, segment %d parameters: Target Temp: %0.2f, Rate: %0.2f," %
          ( RunID, Seg, TargetTmp, Rate ))
        L.info( "  Hold Minutes: %d, Window Seconds: %d" %
          ( HoldMin, Window ))

        StTime=time.strftime('%Y-%m-%d %H:%M:%S')
        L.debug("Update run id %d, segment %d start time to %s" % ( RunID, Seg, StTime ) )
        SQL = "UPDATE Segments SET start_time='%s' where run_id=%d and segment=%d" % ( StTime, RunID, Seg )
        try:
          SQLCur.execute(SQL)
          SQLConn.commit()
        except:
          SQLConn.rollback()
          L.error("DB Update failed!")
  
        Fire(RunID,Seg,TargetTmp,Rate,HoldMin,Window,Kp,Ki,Kd)
        GPIO.output(4,False) ## Turn off GPIO pin 7
  
        EndTime=time.strftime('%Y-%m-%d %H:%M:%S')
        L.debug("Update run id %d, segment %d end time to %s" % ( RunID, Seg, EndTime ) )
        SQL = "UPDATE Segments SET end_time='%s' where run_id=%d and segment=%d" % ( EndTime, RunID, Seg )
        try:
          SQLCur.execute(SQL)
          SQLConn.commit()
        except:
          SQLConn.rollback()
          L.error("DB Update failed!")

    if SegCompStat == 1:
        L.info("Profile stopped - Not updating profile end time")

    else:
      EndTime=time.strftime('%Y-%m-%d %H:%M:%S')
      L.debug("Update profile end time to %s and state to 'Completed' for run id %d" % ( EndTime, RunID ) )
      SQL = "UPDATE Profiles SET end_time='%s', state='Completed' where run_id=%d" % ( EndTime, RunID )
      try:
        SQLCur.execute(SQL)
        SQLConn.commit()
      except:
        SQLConn.rollback()
        L.error("DB Update failed!")

    SegCompStat = 0

    L.info("Polling for 'Running' firing profiles...")

  SQLConn.close()
  time.sleep(2)

