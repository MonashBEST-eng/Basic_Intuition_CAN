#include <SPI.h>
#include <mcp_can.h>

constexpr byte CAN_CS_PIN = 10;

MCP_CAN CAN0(CAN_CS_PIN);

void setup()
{
    Serial.begin(115200);
    delay(500);

    Serial.println("Initialising MCP2515...");

    while (CAN0.begin(MCP_ANY, CAN_125KBPS, MCP_8MHZ) != CAN_OK)
    {
        Serial.println("MCP2515 initialisation failed. Retrying...");
        delay(1000);
    }

    CAN0.setMode(MCP_NORMAL);

    Serial.println("MCP2515 initialised.");
    Serial.println("Polling for CAN messages...");
}

void loop()
{
    if (CAN0.checkReceive() == CAN_MSGAVAIL)
    {
        unsigned long canId = 0;
        byte len = 0;
        byte data[8] = {0};

        byte result = CAN0.readMsgBuf(&canId, &len, data);

        if (result != CAN_OK)
        {
            Serial.print("Read failed: ");
            Serial.println(result);
            return;
        }

        if (len > 8)
        {
            Serial.print("Invalid DLC: ");
            Serial.println(len);
            Serial.println("Likely SPI wiring or MCP2515 communication fault.");
            delay(100);
            return;
        }

        Serial.print("ID: 0x");
        Serial.print(canId, HEX);

        Serial.print(" | DLC: ");
        Serial.print(len);

        Serial.print(" | Data: ");

        for (byte i = 0; i < len; i++)
        {
            if (data[i] < 0x10)
            {
                Serial.print('0');
            }

            Serial.print(data[i], HEX);
            Serial.print(' ');
        }

        Serial.println();
    }
}