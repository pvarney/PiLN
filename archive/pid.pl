#!/usr/bin/perl

use strict;
use warnings;
use Time::HiRes qw(usleep);
use Device::BCM2835;

my $Kp = 1;
my $Ki = 0;
my $Kd = 0;

my $SetTmp = $ARGV[0]; # Final Temp
my $Rate = $ARGV[1]; # Degrees/hour
my $HoldMin = $ARGV[2]; # Minutes to hold temp once reached
my $IntSec = $ARGV[3];

if ( ! defined $SetTmp || ! defined $Rate || ! defined $HoldMin || ! defined $IntSec )
{
  print "\n\nSyntax $0 TargetTemp Rate HoldMinutes IntervalSec\n\n";
  exit 1;
}

my $HoldSec = $HoldMin * 60;
my $RampMin = 0;
my $RampTmp = 0;
my $StartTmp = 0;
my $TmpDif = 0;
my $Steps = 0;
my $StepTmp = 0;
my $LastErr = 0;
my $StartSec = 0;
my $EndSec = 0;
my $NextInt = 0;

Device::BCM2835::init() || die "Could not init BCM2835\n";

# Set RPi pin 11 to be an output
Device::BCM2835::gpio_fsel(&Device::BCM2835::RPI_GPIO_P1_11, &Device::BCM2835::BCM2835_GPIO_FSEL_OUTP);

sub Update
{
  
  my $SP = shift;
  my $PV = shift;
  my $IMax = shift;
  my $IMin = shift;

  my $Err = $SP - $PV;

  my $Pterm = $Kp * $Err;

  my $IState += ( $Err * $IntSec );

  if ( $IState > $IMax )
  {

    $IState = $IMax;

  }
  elsif ( $IState < $IMin )
  {

    $IState = $IMin;

  }

  my $Iterm = $Ki * $IState;

  my $Dterm = $Kd * ( ( $Err - $LastErr ) / $IntSec );
  $LastErr = $Err;

  return $Pterm + $Iterm + $Dterm;

}


print "===Start===\n";
my $Cnt = 0;

while ( time() <= $EndSec || $StartSec == 0 )
{

  usleep ( 10_000 );

  if ( time() >= $NextInt )
  {

    $Cnt++;
    $NextInt += $IntSec;
    $RampTmp += $StepTmp unless ( $RampTmp >= $SetTmp );

    my ( $ReadTmp, $ReadITmp ) = split ( /,/, `/home/kiln_cont/gettemp.py` );
    my $Output = &Update($SetTmp,$ReadTmp,100,0);
  
    if ( $StartTmp == 0 )
    {

      $StartTmp = $ReadTmp;
      $StartSec = time();
      $NextInt = $StartSec + $IntSec;
      $TmpDif = $SetTmp - $StartTmp;
      $RampMin = ( $TmpDif / $Rate ) * 60;
      $Steps = ( $RampMin * 60 ) / $IntSec;
      $StepTmp =  $TmpDif / $Steps;
      $EndSec = $StartSec + ( $RampMin * 60 ) + ( $HoldMin * 60 );
      $RampTmp = $StartTmp + $StepTmp;
      
      print "    Set Temp: $SetTmp\n";
      print "  Start Temp: $StartTmp\n";
      print " Temp Change: $TmpDif\n";
      print "Ramp Minutes: $RampMin\n";
      print "       Steps: $Steps\n";
      print "   Step Temp: $StepTmp\n";
      print "    Interval: $IntSec\n";
      print "    StartSec: $StartSec\n";
      print "      EndSec: $EndSec\n\n";

    }

    printf "%5.5d - Temp: %5.2f  SetTemp: %5.2f  Target: %5.2f  Output: %5.2f\n", $Cnt, $ReadTmp, $RampTmp, $SetTmp, $Output;

    my $CycleOnMS  = 1000000 * ( $IntSec * ( $Output * 0.01 ) );
#    $CycleOnMS =~ s/(\d\d\d)$/_\1/;
#    $CycleOnMS =~ s/(\d\d\d)_/_\1_/g;
    print " ==> On for $CycleOnMS\n";
    Device::BCM2835::gpio_write(&Device::BCM2835::RPI_GPIO_P1_11, 1);
    usleep ( $CycleOnMS );
    print " ==> Off\n";
    Device::BCM2835::gpio_write(&Device::BCM2835::RPI_GPIO_P1_11, 0);

  }
  
}
