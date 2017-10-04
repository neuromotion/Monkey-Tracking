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
uint64_t gridState = 0x0001;
int tally = 0;

//// Timer Variable Create an IntervalTimer object 
IntervalTimer onTimer;
IntervalTimer offTimer;

void setup() {
  // put your setup code here, to run once:
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

  onTimer.begin(refreshGrid, 1e3);
  delayMicroseconds(800);
  offTimer.begin(endTx, 1e3);
}

void loop() {
  // put your main code here, to run repeatedly:
}

void longLongShiftOut(uint8_t dataPin, uint8_t clockPin, uint8_t bitOrder, uint64_t val)
{
  uint8_t i;
  
  for (i = 0; i < 64; i++)  {
    
    if (bitOrder == LSBFIRST){
      digitalWrite(dataPin, !!(val & (1LL << i)));
    }
    else{
      digitalWrite(dataPin, !!(val & (1LL << (63 - i))));
    }
      
    digitalWrite(clockPin, HIGH);
    digitalWrite(clockPin, LOW);    
  }
}
// Interrupt is called once a millisecond, looks for any new GPS data, and stores it

void refreshGrid(void)
{
  // take the latchPin low so 
  // the LEDs don't change while you're sending in bits:
  
  digitalWrite(gridLatchPin, LOW);
  digitalWrite(tallyLatchPin, LOW);

  //increment the grid
  gridState = gridState << 1;
  //shift the grid state out
  longLongShiftOut(gridDataPin, gridClockPin, LSBFIRST, gridState);
  //shift the clock out
  shiftOut(tallyDataPin, tallyClockPin, LSBFIRST, tally);
  
  if (gridState == 0){
    gridState = 0x0001;
    tally++;
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

