#include <ArduinoBLE.h>
#include "Nano33BLEAccelerometer.h"
Nano33BLEAccelerometerData accelerometerData;

BLEService accService("23eb800f-b617-44b6-8641-f64022b42e98"); // BLE Acc Service

// BLE LED Switch Characteristic - custom 128-bit UUID, read and writable by central
BLEFloatCharacteristic accxCharacteristic("9986d2ad-33ba-4dcc-8b2b-e25a021c04e0", BLERead | BLENotify);
BLEFloatCharacteristic accyCharacteristic("ec754736-18ec-40ee-9b55-6f543d924ac2", BLERead | BLENotify);
BLEFloatCharacteristic acczCharacteristic("7baa72e5-50d4-424e-9d9e-9d19986b1e87", BLERead | BLENotify);

long previousMillis = 0;  // last time the battery level was checked, in ms

void setup() {
  // Serial
  Serial.begin(9600);
  while (!Serial);

  // IMU
  Accelerometer.begin();  
  
  // begin initialization
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");

    while (1);
  }
  
  // set advertised local name and service UUID:
  BLE.setLocalName("Acc");
  BLE.setAdvertisedService(accService);

  // add the characteristic to the service
  accService.addCharacteristic(accxCharacteristic);
  accService.addCharacteristic(accyCharacteristic);
  accService.addCharacteristic(acczCharacteristic);

  // add service
  BLE.addService(accService);

  // start advertising
  BLE.advertise();
  
  Serial.println("BLE Acc Peripheral");
}

void loop() {
  // listen for BLE peripherals to connect:
  BLEDevice central = BLE.central();

  // if a central is connected to peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    //prints the centrals MAC address:
    Serial.println(central.address());

    // while the central is still connected to peripheral:
    while (central.connected()) {
      long currentMillis = millis();
      // if 1000ms have passed, check the battery level:
      if (currentMillis - previousMillis >= 2000) {
        previousMillis = currentMillis;
        if(Accelerometer.pop(accelerometerData)){
           Serial.printf("%f,%f,%f\r\n", accelerometerData.x, accelerometerData.y, accelerometerData.z);
           accxCharacteristic.writeValue(accelerometerData.x);
           accyCharacteristic.writeValue(accelerometerData.y);
           acczCharacteristic.writeValue(accelerometerData.z);
        }
      }
    }

    // when the central disconnects, print it out:
    Serial.print(F("Disconnected from central: "));
    Serial.println(central.address());
  }
}
