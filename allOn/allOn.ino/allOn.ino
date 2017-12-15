/*
 * Code to drive an array of LEDs in order to synchronize Kinect recordings to neural data
 */

// Pin connected to ST_CP of 74HC595
int gridLatchPin = 6;
int tallyLatchPin = 10;

// Pin connected to SH_CP of 74HC595
int gridClockPin = 5;
int tallyClockPin = 9;

//// Pin connected to DS of 74HC595
int gridDataPin = 4;
int tallyDataPin = 8;

//// Pins connected to OE
int gridOutputEnable = 7;
int tallyOutputEnable = 11;

//// Variable contains the 64bit number to be displayed on the grid
int currentGridBlock = 0;
uint8_t gridState[12];
int tally = 0;
uint8_t tallyBin[2];

//// Timer Variable Create an IntervalTimer object 
IntervalTimer onTimer;
IntervalTimer offTimer;

void setup() {
  // put your setup code here, to run once:
  memset(gridState,0,sizeof(gridState));
  gridState[currentGridBlock] = 255;
  memset(tallyBin,255, sizeof(tallyBin));
  
  pinMode(gridLatchPin, OUTPUT);
  pinMode(gridClockPin, OUTPUT);
  pinMode(gridDataPin, OUTPUT);
  
  pinMode(gridOutputEnable, OUTPUT);
  digitalWrite(gridOutputEnable, LOW);
  
  pinMode(tallyLatchPin, OUTPUT);
  pinMode(tallyClockPin, OUTPUT);
  pinMode(tallyDataPin, OUTPUT);
  
  pinMode(tallyOutputEnable, OUTPUT);
  digitalWrite(tallyOutputEnable, LOW);

  onTimer.begin(refreshGrid, 1e6);
  delayMicroseconds(5000);
  offTimer.begin(endTx, 1e6);
}

void loop() {
  // put your main code here, to run repeatedly:
}

void refreshGrid(void)
{
  // take the latchPin low so 
  // the LEDs don't change while you're sending in bits:
  
  digitalWrite(gridLatchPin, LOW);
  digitalWrite(tallyLatchPin, LOW);

  //shift the grid state out
  int i;
  for (i = 0; i < sizeof(gridState); i++) {
    shiftOut(gridDataPin, gridClockPin, LSBFIRST, gridState[i]);
  }
  //shift the clock out
  for (i = 0; i < sizeof(tallyBin); i++) {
    shiftOut(tallyDataPin, tallyClockPin, LSBFIRST, tallyBin[i]);
  }
  
  digitalWrite(gridDataPin, LOW);
  digitalWrite(tallyDataPin, LOW);
}

void endTx(void)
{  
  //take the latch pin high so the LEDs will light up:
  digitalWrite(gridLatchPin, HIGH);
  digitalWrite(tallyLatchPin, HIGH);
  
  digitalWrite(gridDataPin, LOW);
  digitalWrite(tallyDataPin, LOW);
}

