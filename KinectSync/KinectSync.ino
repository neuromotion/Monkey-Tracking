#include <Adafruit_ASFcore.h>
#include <clock.h>
#include <clock_feature.h>
#include <compiler.h>
#include <gclk.h>
#include <i2s.h>
#include <interrupt.h>
#include <interrupt_sam_nvic.h>
#include <parts.h>
#include <pinmux.h>
#include <power.h>
#include <reset.h>
#include <status_codes.h>
#include <system.h>
#include <system_interrupt.h>
#include <system_interrupt_features.h>
#include <tc.h>
#include <tc_interrupt.h>
#include <wdt.h>
#include <Adafruit_ZeroTimer.h>

/*
 * Code to drive an array of LEDs in order to synchronize Kinect recordings to neural data
 */

// Pin connected to ST_CP of 74HC595
int latchPin = 8;
int timerLatchPin = 4;

// Pin connected to SH_CP of 74HC595
int clockPin = 12;
int timerClockPin = 7;

//// Pin connected to DS of 74HC595
int dataPin = 11;
int timerDataPin = 6;

//// Variable contains the 64bit number to be displayed on the grid
uint64_t gridState = 0x0001;
int gridTimer = 0;

//// Timer Variable
Adafruit_ZeroTimer zt3 = Adafruit_ZeroTimer(3);

void setup() {
  // put your setup code here, to run once:
  pinMode(latchPin, OUTPUT);
  pinMode(clockPin, OUTPUT);
  pinMode(dataPin, OUTPUT);
  
  pinMode(timerLatchPin, OUTPUT);
  pinMode(timerClockPin, OUTPUT);
  pinMode(timerDataPin, OUTPUT);
  
  /********************* Timer #3, 16 bit, two PWM outs, period = 65535 */
  zt3.configure(TC_CLOCK_PRESCALER_DIV256, // prescaler
                TC_COUNTER_SIZE_8BIT,   // bit width of timer/counter
                TC_WAVE_GENERATION_NORMAL_PWM   // match style
                );

  zt3.setPeriodMatch(190, 1, 0); // ~350khz, 1 match, channel 0
  zt3.setCallback(true, TC_CALLBACK_CC_CHANNEL0, Timer3Callback0);
  zt3.enable(true);
}

void loop() {
  // put your main code here, to run repeatedly:
}

void longLongShiftOut(uint8_t dataPin, uint8_t clockPin, uint8_t bitOrder, uint64_t val)
{
  uint8_t i;
  digitalWrite(dataPin, LOW);
  
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

void Timer3Callback0(struct tc_module *const module_inst)
{
  // take the latchPin low so 
  // the LEDs don't change while you're sending in bits:
  
  digitalWrite(latchPin, LOW);
  digitalWrite(timerLatchPin, LOW);

  //increment the grid
  gridState = gridState << 1;
  //shift the grid state out
  longLongShiftOut(dataPin, clockPin, LSBFIRST, gridState);
  //shift the clock out
  shiftOut(timerDataPin, timerClockPin, LSBFIRST, gridTimer);
  
  if (gridState == 0){
    gridState = 0x0001;
    gridTimer++;
  }
  else{
    //gridState = gridState;
    //gridTimer = gridTimer;
  }
  
  //take the latch pin high so the LEDs will light up:
  digitalWrite(latchPin, HIGH);
  digitalWrite(timerLatchPin, HIGH);
  
  digitalWrite(dataPin, LOW);
  digitalWrite(timerDataPin, LOW);
} 
