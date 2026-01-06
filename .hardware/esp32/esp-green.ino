#include <WiFi.h>

const char ssid = "BrainMoveG1";
const char pass = "bmhotspotajm";

void setup() {
  Serial.begin(115200);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Verbinden met RPi Hotspot");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("Verbonden!");
  Serial.print("IP-adres (IP address): ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Jouw code hier
}