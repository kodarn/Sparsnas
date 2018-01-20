//============================================================================
// Filename: SparsnasLedBlinker.ino
// Purpose:  Provide a configurable led blinking pulse as a help for decoding
//           the transmitted packet data.
//============================================================================

//----------------------------------------------------------------------------
//------------------------------- Include Files ------------------------------
//----------------------------------------------------------------------------
#include <Button.h>
#include <Wire.h> 
#include <RtcDS3231.h>
#include "U8glib.h"

//----------------------------------------------------------------------------
//----------------------------- Global variables -----------------------------
//----------------------------------------------------------------------------
Button                IncButton(7);
Button                DecButton(8);
U8GLIB_SSD1306_128X64 oled(U8G_I2C_OPT_NONE);
RtcDS3231<TwoWire>    rtcObject(Wire);

const byte            wakePin     = 2;
const byte            ledPin      = 3;

byte                  hours       = 0;
byte                  minutes     = 0;
byte                  seconds     = 0;
byte                  blinkDelay  = 1;
byte                  secondCnt   = 0;
volatile bool         alarmFlag   = false;

//----------------------------------------------------------------------------
// updateTime
//----------------------------------------------------------------------------
void updateTime()
{
  RtcDateTime now = rtcObject.GetDateTime();
  hours = now.Hour();
  minutes = now.Minute();
  seconds = now.Second();
}

//----------------------------------------------------------------------------
// updateDisplay
//----------------------------------------------------------------------------
void updateDisplay()
{
  char timeString[32];

  oled.setFont(u8g_font_helvB10);

  sprintf(timeString, "Time: %02u:%02u:%02u", hours, minutes, seconds);
  oled.setPrintPos(0, 20);
  oled.print(timeString);

  sprintf(timeString, "BlinkDelay: %u", blinkDelay);
  oled.setPrintPos(0, 45);
  oled.print(timeString);
}

//----------------------------------------------------------------------------
// handleRtcAlarm
//----------------------------------------------------------------------------
void handleRtcAlarm() 
{
  alarmFlag = false;
  rtcObject.LatchAlarmsTriggeredFlags();
 
  secondCnt++;
  if (blinkDelay == 0) {
    secondCnt = 0;
  }

  if (blinkDelay > 0)
  {
    if (secondCnt == blinkDelay)
    {
      secondCnt = 0;
      digitalWrite(ledPin, HIGH);    // flash the led
      delay(100);                    // wait a little bit
      digitalWrite(ledPin, LOW);     // turn off led  
    }
  }
}

//----------------------------------------------------------------------------
// handleInterrupt
//----------------------------------------------------------------------------
void handleInterrupt() 
{
  // Try to do as little as possible in this ISR
  alarmFlag = true;
}

//----------------------------------------------------------------------------
// setup
//----------------------------------------------------------------------------
void setup() 
{
  // Initialize global variables
  blinkDelay = 1;
  secondCnt = 0;

  // Initialize push buttons
  IncButton.begin();
  DecButton.begin();

  // Initialize pins
  pinMode(ledPin, OUTPUT); // 
  pinMode(wakePin, INPUT); // 
  // Initialize the RTC and the alarm associated with it.
  DS3231AlarmOne alarm1(0,0,0,0,DS3231AlarmOneControl_OncePerSecond);
  rtcObject.Begin();
  if (!rtcObject.GetIsRunning())
  {
    Serial.println(F("WARNING: RTC was not actively running, starting it now."));
    rtcObject.SetIsRunning(true);
  }
  rtcObject.Enable32kHzPin(false);
  rtcObject.SetSquareWavePin(DS3231SquareWavePin_ModeAlarmOne);
  rtcObject.SetAlarmOne(alarm1);
  rtcObject.LatchAlarmsTriggeredFlags();

  // Uncomment this if you want to set the current time
  //Wire.begin();
  //RtcDateTime compileTime = RtcDateTime(__DATE__, __TIME__);
  //rtcModule.SetDateTime(compileTime);

  // Enable the interrupthandler to trigger when wakePin is signaled by the
  // RTC-hardware; see the board layout image for details.
  // Note that the interrupt mode is FALLING because the alarm interrupt in
  // the DS3231 is active-low.
  attachInterrupt(digitalPinToInterrupt(wakePin), handleInterrupt, FALLING);
}

//----------------------------------------------------------------------------
// loop
//----------------------------------------------------------------------------
void loop() 
{
  // Check buttons
  if (IncButton.pressed()) {
    blinkDelay++;
  }
  if (DecButton.pressed()) {
    blinkDelay--;
  }

  // Check if the RTC alarm has been triggered
  if (alarmFlag == true) {
    handleRtcAlarm();
  }

  // Update time values
  updateTime();

  // Update the display
  oled.firstPage();
  do {
    updateDisplay();  
  } while (oled.nextPage());

  // Take a small break and relax
  delay(20);
}
