/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : CAN request/response handshake with UART diagnostics
  ******************************************************************************
  */
/* USER CODE END Header */

#include "main.h"

/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

#define CAN_REQUEST_ID   0x123U
#define CAN_RESPONSE_ID  0x124U

CAN_HandleTypeDef hcan1;
UART_HandleTypeDef huart1;

void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_CAN1_Init(void);
static void MX_USART1_UART_Init(void);
static void UART_Print(const char *text);
static void CAN_ConfigFilter(void);
static HAL_StatusTypeDef CAN_SendResponse(const uint8_t *request_data,
                                          uint8_t request_dlc);

static void UART_Print(const char *text)
{
  if (text == NULL)
  {
    return;
  }

  (void)HAL_UART_Transmit(&huart1,
                          (uint8_t *)text,
                          (uint16_t)strlen(text),
                          HAL_MAX_DELAY);
}

static void CAN_ConfigFilter(void)
{
  CAN_FilterTypeDef filter = {0};

  filter.FilterBank = 0;
  filter.FilterMode = CAN_FILTERMODE_IDMASK;
  filter.FilterScale = CAN_FILTERSCALE_32BIT;
  filter.FilterIdHigh = (uint16_t)(CAN_REQUEST_ID << 5);
  filter.FilterIdLow = 0x0000U;
  filter.FilterMaskIdHigh = (uint16_t)(0x7FFU << 5);
  filter.FilterMaskIdLow = 0x0000U;
  filter.FilterFIFOAssignment = CAN_RX_FIFO0;
  filter.FilterActivation = ENABLE;
  filter.SlaveStartFilterBank = 14;

  if (HAL_CAN_ConfigFilter(&hcan1, &filter) != HAL_OK)
  {
    UART_Print("CAN filter configuration FAILED\r\n");
    Error_Handler();
  }
}

static HAL_StatusTypeDef CAN_SendResponse(const uint8_t *request_data,
                                          uint8_t request_dlc)
{
  CAN_TxHeaderTypeDef tx_header = {0};
  uint8_t tx_data[8] = {0};
  uint32_t tx_mailbox = 0U;

  if ((request_data == NULL) || (request_dlc > 8U))
  {
    return HAL_ERROR;
  }

  tx_header.StdId = CAN_RESPONSE_ID;
  tx_header.ExtId = 0U;
  tx_header.IDE = CAN_ID_STD;
  tx_header.RTR = CAN_RTR_DATA;
  tx_header.DLC = request_dlc;
  tx_header.TransmitGlobalTime = DISABLE;

  memcpy(tx_data, request_data, request_dlc);

  if (HAL_CAN_GetTxMailboxesFreeLevel(&hcan1) == 0U)
  {
    return HAL_BUSY;
  }

  return HAL_CAN_AddTxMessage(&hcan1,
                              &tx_header,
                              tx_data,
                              &tx_mailbox);
}

int main(void)
{
  CAN_RxHeaderTypeDef rx_header = {0};
  uint8_t rx_data[8] = {0};
  char uart_message[192];

  HAL_Init();
  SystemClock_Config();

  MX_GPIO_Init();
  MX_CAN1_Init();
  MX_USART1_UART_Init();

  UART_Print("\r\nSTM32 CAN handshake starting...\r\n");

  CAN_ConfigFilter();

  if (HAL_CAN_Start(&hcan1) != HAL_OK)
  {
    UART_Print("HAL_CAN_Start FAILED\r\n");
    Error_Handler();
  }

  UART_Print("CAN started at 500 kbit/s\r\n");
  UART_Print("Waiting for ID 0x123; replying on ID 0x124\r\n");

  while (1)
  {
    if (HAL_CAN_GetRxFifoFillLevel(&hcan1, CAN_RX_FIFO0) > 0U)
    {
      if (HAL_CAN_GetRxMessage(&hcan1,
                               CAN_RX_FIFO0,
                               &rx_header,
                               rx_data) == HAL_OK)
      {
        if ((rx_header.IDE == CAN_ID_STD) &&
            (rx_header.RTR == CAN_RTR_DATA) &&
            (rx_header.StdId == CAN_REQUEST_ID))
        {
          (void)snprintf(
              uart_message,
              sizeof(uart_message),
              "RX acknowledged: ID=0x%03lX DLC=%lu "
              "DATA=%02X %02X %02X %02X %02X %02X %02X %02X\r\n",
              (unsigned long)rx_header.StdId,
              (unsigned long)rx_header.DLC,
              rx_data[0], rx_data[1], rx_data[2], rx_data[3],
              rx_data[4], rx_data[5], rx_data[6], rx_data[7]);

          UART_Print(uart_message);

          HAL_StatusTypeDef tx_status =
              CAN_SendResponse(rx_data, (uint8_t)rx_header.DLC);

          if (tx_status == HAL_OK)
          {
            UART_Print("TX response queued: ID=0x124\r\n");
            HAL_GPIO_TogglePin(LD3_GPIO_Port, LD3_Pin);
          }
          else
          {
            (void)snprintf(
                uart_message,
                sizeof(uart_message),
                "TX response FAILED: HAL=%d CAN_error=0x%08lX "
                "ESR=0x%08lX TSR=0x%08lX\r\n",
                (int)tx_status,
                (unsigned long)HAL_CAN_GetError(&hcan1),
                (unsigned long)hcan1.Instance->ESR,
                (unsigned long)hcan1.Instance->TSR);

            UART_Print(uart_message);
          }
        }
      }
    }

    HAL_Delay(5U);
  }
}

void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_MSI;
  RCC_OscInitStruct.MSIState = RCC_MSI_ON;
  RCC_OscInitStruct.MSICalibrationValue = 0;
  RCC_OscInitStruct.MSIClockRange = RCC_MSIRANGE_6;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_MSI;
  RCC_OscInitStruct.PLL.PLLM = 1;
  RCC_OscInitStruct.PLL.PLLN = 16;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV7;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;

  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK |
                                RCC_CLOCKTYPE_SYSCLK |
                                RCC_CLOCKTYPE_PCLK1 |
                                RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_1) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_CAN1_Init(void)
{
  hcan1.Instance = CAN1;
  hcan1.Init.Prescaler = 4;
  hcan1.Init.Mode = CAN_MODE_NORMAL;
  hcan1.Init.SyncJumpWidth = CAN_SJW_1TQ;
  hcan1.Init.TimeSeg1 = CAN_BS1_13TQ;
  hcan1.Init.TimeSeg2 = CAN_BS2_2TQ;
  hcan1.Init.TimeTriggeredMode = DISABLE;
  hcan1.Init.AutoBusOff = ENABLE;
  hcan1.Init.AutoWakeUp = DISABLE;
  hcan1.Init.AutoRetransmission = ENABLE;
  hcan1.Init.ReceiveFifoLocked = DISABLE;
  hcan1.Init.TransmitFifoPriority = DISABLE;

  if (HAL_CAN_Init(&hcan1) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_USART1_UART_Init(void)
{
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;

  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  HAL_GPIO_WritePin(LD3_GPIO_Port, LD3_Pin, GPIO_PIN_RESET);

  GPIO_InitStruct.Pin = LD3_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LD3_GPIO_Port, &GPIO_InitStruct);
}

void Error_Handler(void)
{
  __disable_irq();
  while (1)
  {
  }
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  (void)file;
  (void)line;
}
#endif
