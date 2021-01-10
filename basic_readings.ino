#include <SPI.h>
#include "RF24.h"
#include<Wire.h>

// Init radio object
RF24 radio(9, 10);
const uint64_t pipes[1] = { 0xF0F0F0F0E1LL }; // Radio pipe addresses for the 2 nodes to communicate.
bool xmit_data = false;

// Loop timing
unsigned long previousMillis = millis();
const long interval = 2;
bool mode = false;

// Define MPU variables
const int MPU6050_addr=0x68;
int16_t AccX, AccY, AccZ;
struct acc_xyz {
  int16_t acc_x;
  int16_t acc_y;
  int16_t acc_z;
};
struct acc_xyz samples[200] = {0};
bool impact_detected = false;
int samples_counter = 0;

void setup(void) {
  //Serial.begin(115200);
  //while (!Serial)
  //  delay(10); 
  
  // start radio  
  radio.begin();
  radio.setDataRate(RF24_2MBPS);
  radio.setPALevel(RF24_PA_MIN);
  radio.enableDynamicPayloads();
  radio.setRetries(5, 15);
  radio.openWritingPipe(pipes[0]);

  // reset IMU
  Wire.begin();
  Wire.beginTransmission(MPU6050_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  // set max bandwidth
  Wire.begin();
  Wire.beginTransmission(MPU6050_addr);
  Wire.write(0x1A);
  Wire.write(0);
  Wire.endTransmission(true);

  // set range to +-16g
  Wire.beginTransmission(MPU6050_addr);
  Wire.write(0x1C);
  Wire.write(0x18);
  Wire.endTransmission(true);
    
  delay(100);
}

void loop() {
  unsigned long currentMillis = millis();
   
  if (currentMillis - previousMillis >= interval) { //
    // Get new sensor events with the readings
    Wire.beginTransmission(MPU6050_addr);
    Wire.write(0x3B);
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_addr, 6, true);
    AccX=Wire.read()<<8|Wire.read();
    AccY=Wire.read()<<8|Wire.read();
    AccZ=Wire.read()<<8|Wire.read();

    if (abs(AccZ - 1860) > 300 || !mode) {
      impact_detected = true;
      
    }
  
    if (impact_detected) {
      samples[samples_counter].acc_x = AccX;
      samples[samples_counter].acc_y = AccY;
      samples[samples_counter].acc_z = AccZ;
      samples_counter++;
      if (samples_counter >= 200) {
        impact_detected = false;
        samples_counter = 0;
        xmit_data = true;
      }
    }
    previousMillis = currentMillis;
  }

  if (xmit_data) {
    radio.write(&mode, sizeof(mode));
    for (int i = 0; i < 200; i++) {
      radio.write(&samples[i], sizeof(samples[i]));
    }
    xmit_data = false;
    mode = true;
  }
}
