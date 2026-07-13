#include <SPI.h>
#include <mcp_can.h>

#define CAN_CS_PIN 10

MCP_CAN CAN(CAN_CS_PIN);

void setup()
{
    Serial.begin(115200);

    Serial.println("Initialising MCP2515...");

    while (CAN.begin(MCP_ANY, CAN_125KBPS, MCP_8MHZ) != CAN_OK)
    {
        Serial.println("MCP2515 initialisation failed. Retrying...");
        delay(1000);
    }

    CAN.setMode(MCP_NORMAL);

    Serial.println("MCP2515 initialised.");
    Serial.println("Sending CAN frames...");
}

void loop()
{
    // Eight data bytes
    byte data[8] = {
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08
    };

    // Standard 11-bit CAN identifier
    unsigned long canId = 0x123;

    byte result = CAN.sendMsgBuf(
        canId,  // CAN ID
        0,      // 0 = standard 11-bit frame
        8,      // Data length
        data    // Data bytes
    );

    if (result == CAN_OK)
    {
        Serial.println("CAN frame sent.");
    }
    else
    {
        Serial.print("CAN send failed. Error code: ");
        Serial.println(result);
    }

    delay(1000);
}