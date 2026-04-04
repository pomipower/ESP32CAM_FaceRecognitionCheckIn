#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include <LiquidCrystal.h>
#include "soc/soc.h"           
#include "soc/rtc_cntl_reg.h"  

// === NETWORK SETUP (USE MOBILE HOTSPOT) ===
const char* ssid = "WIFI_NAME";
const char* password = "PASSWORD";
const char* serverName = "http://[IP_ADDRESS]/clock_in"; // YOUR PC IP

// === PIN SETUP ===
const int BUTTON_PIN = 1; // The Push Button

// LCD Pins
const int rs = 14, en = 15, d4 = 13, d5 = 12, d6 = 2, d7 = 3;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);
const int contrastPin = 4; 
const int pwmFreq = 5000;
const int pwmResolution = 8; 
int contrastValue = 80; 

// Camera Pins
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); 
  delay(5000); // Wait 5s for hot-plug!

  Serial.begin(115200);
  
  // Set Button Pin
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // Setup LCD
  ledcAttach(contrastPin, pwmFreq, pwmResolution);
  ledcWrite(contrastPin, contrastValue);
  lcd.begin(16, 2);
  lcd.print("Booting Security");

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  lcd.setCursor(0, 1);
  lcd.print("Connecting WiFi.");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  // Setup Camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_1;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM; config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM; config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM; config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 1;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_camera_init(&config);
  
  lcd.clear();
  lcd.print("READY. Press BTN");
  lcd.setCursor(0, 1);
  lcd.print("to clock in ->");

  Serial.end(); 
  pinMode(BUTTON_PIN, INPUT_PULLUP);
}

void loop() {
  // Wait indefinitely until the button is pressed
  if (digitalRead(BUTTON_PIN) == LOW) {
    lcd.clear();
    lcd.print("Scanning Face...");
    
    // 1. Safely flush out the old hardware buffer
    camera_fb_t * stale_fb = esp_camera_fb_get();
    if (stale_fb) {
      esp_camera_fb_return(stale_fb);
    }

    // 2. Give the sensor 200ms to adjust Auto-Exposure and Auto-White Balance
    delay(200);

    // 3. Capture the brand new, perfectly exposed frame
    camera_fb_t * fb = esp_camera_fb_get();
    
    if (!fb) {
      lcd.setCursor(0, 1);
      lcd.print("Cam Error");
      delay(2000);
      return;
    }

    lcd.clear();
    lcd.print("Authorizing...");

    // Send to Python
    WiFiClient client;
    HTTPClient http;
    http.begin(client, serverName);
    http.addHeader("Content-Type", "image/jpeg"); 
    
    int httpResponseCode = http.POST(fb->buf, fb->len);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      
      // Split the Python response at the newline character '\n'
      int splitIndex = response.indexOf('\n');
      String line1 = response.substring(0, splitIndex);
      String line2 = response.substring(splitIndex + 1);

      lcd.clear();
      lcd.print(line1);
      lcd.setCursor(0, 1);
      lcd.print(line2);
      
    } else {
      lcd.clear();
      lcd.print("Network Error");
    }

    http.end();
    esp_camera_fb_return(fb);

    // Wait 5 seconds so they can read the result, then reset
    delay(5000); 
    lcd.clear();
    lcd.print("READY. Press BTN");
    lcd.setCursor(0, 1);
    lcd.print("to clock in ->");
    
    // Wait for them to let go of the button so it doesn't loop
    while(digitalRead(BUTTON_PIN) == LOW) { delay(10); } 
  }
}