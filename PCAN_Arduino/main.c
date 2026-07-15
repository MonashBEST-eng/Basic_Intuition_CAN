
CAN_Frame requestFrame = {0};

HAL_StatusTypeDef rxStatus =
    MCP2515_ReadMessage(&requestFrame);

if (rxStatus == HAL_OK)
{
    printf(
        "H7 RX | ID=0x%lX | DLC=%u | Data:",
        requestFrame.id,
        requestFrame.dlc
    );

    for (uint8_t i = 0; i < requestFrame.dlc; i++)
    {
        printf(" %02X", requestFrame.data[i]);
    }

    printf("\r\n");

    if (!requestFrame.ext &&
        !requestFrame.rtr &&
        requestFrame.id == 0x123)
    {
        CAN_Frame responseFrame = {0};

        responseFrame.id = 0x124;
        responseFrame.ext = 0;
        responseFrame.rtr = 0;
        responseFrame.dlc = requestFrame.dlc;

        for (uint8_t i = 0; i < requestFrame.dlc; i++)
        {
            responseFrame.data[i] =
                requestFrame.data[i];
        }

        HAL_Delay(200);

        HAL_StatusTypeDef txStatus =
            MCP2515_SendMessage(&responseFrame);

        if (txStatus == HAL_OK)
        {
            printf(
                "H7 TX | ID=0x%lX | DLC=%u | Data:",
                responseFrame.id,
                responseFrame.dlc
            );

            for (uint8_t i = 0;
                    i < responseFrame.dlc;
                    i++)
            {
                printf(" %02X",
                        responseFrame.data[i]);
            }

            printf("\r\n");
        }
        else
        {
            printf(
                "H7 TX failed, status=%d\r\n",
                txStatus
            );
        }
    }
}

HAL_Delay(1);