/*
 * Code to drive an array of LEDs in order to synchronize Kinect recordings to neural data
 */

bool debugging = 1;
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
int startInterruptPin = 32;
IntervalTimer onTimer;
IntervalTimer offTimer;

void setup() {
  if (debugging) {
    Serial.begin(9600);      // open the serial port at 9600 bps: 
  }
  
  // put your setup code here, to run once:
  memset(gridState,0,sizeof(gridState));
  gridState[0] = 1;
  memset(tallyBin, 0, sizeof(tallyBin));
  
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

  startDisplay();
  //pinMode(startInterruptPin, INPUT_PULLUP); // sets the digital pin as output
  //digitalWrite(startInterruptPin, HIGH);
  //attachInterrupt(startInterruptPin, startDisplay, FALLING); // interrrupt 1 is data ready
}

void loop() {
  // put your main code here, to run repeatedly:
}

void startDisplay(void){
  Serial.println("Starting timed interrupts...");
  
  int i,j;
  
  uint8_t flash = 255;
  // Light all LEDs
    
  for (j = 0; j < 4; j++) {
    digitalWrite(gridLatchPin, LOW);
    digitalWrite(tallyLatchPin, LOW);
    
    for (i = 0; i < 2; i++) {
      shiftOut(tallyDataPin, tallyClockPin, LSBFIRST, flash);
    }
    for (i = 0; i < 12; i++) {
      shiftOut(gridDataPin, gridClockPin, LSBFIRST, flash);
    }
  
    //take the latch pin high so the LEDs will light up:
    digitalWrite(gridLatchPin, HIGH);
    digitalWrite(tallyLatchPin, HIGH);
  
    digitalWrite(gridDataPin, LOW);
    digitalWrite(tallyDataPin, LOW);

    if (flash == 255) {
      flash = 0;
    }
    else if (flash == 0)
    {
      flash = 255;
    }
  
    delay(1000);
    
    Serial.println(j);
  }
  
  onTimer.begin(refreshGrid, 0.9e3);
  delayMicroseconds(500);
  offTimer.begin(endTx, 0.9e3);

}

void refreshGrid(void)
{
  // take the latchPin low so 
  // the LEDs don't change while you're sending in bits:
  
  digitalWrite(gridLatchPin, LOW);
  digitalWrite(tallyLatchPin, LOW);

  if (gridState[currentGridBlock] == 0){
    // shift to the next block
    currentGridBlock++;
    gridState[currentGridBlock] = 1;
  }
  
  //shift the grid state out
  int i;
  for (i = 0; i < sizeof(gridState); i++) {
    shiftOut(gridDataPin, gridClockPin, LSBFIRST, gridState[i]);
  }
  //shift the clock out
  for (i = 0; i < sizeof(tallyBin); i++) {
    shiftOut(tallyDataPin, tallyClockPin, LSBFIRST, tallyBin[i]);
  }
  
  //increment the grid
  gridState[currentGridBlock] = gridState[currentGridBlock] << 1; 
    
  if (currentGridBlock == sizeof(gridState) - 1){
    currentGridBlock = 0;
    gridState[currentGridBlock] = 1;
    tally++;
    tallyBin[0] = highByte(tally);
    tallyBin[1] = lowByte(tally);
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

