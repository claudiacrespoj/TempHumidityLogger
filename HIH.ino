
#include <HIH61XX.h>

#include <AsyncDelay.h>



#include <HIH61XXCommander.h>

#include <Wire.h>






//  Create an HIH61XX with I2C address 0x27, powered by 3.3V pin

HIH61XX hih(0x27);





void setup()

{

  Serial.begin(115200);

  Wire.begin();

}





void loop()

{

  //  start the sensor

  hih.start();



  //  request an update of the humidity and temperature

  hih.update();



  Serial.print("Humidity: ");

  Serial.print(hih.humidity(), 5);

  Serial.print(" RH (");

  Serial.print(hih.humidity_Raw());

  Serial.println(")");



  Serial.print("Temperature: ");

  Serial.print(hih.temperature(), 5);

  Serial.println(" C (");

  Serial.print(hih.temperature_Raw());

  Serial.println(")");



  while(true);

}
