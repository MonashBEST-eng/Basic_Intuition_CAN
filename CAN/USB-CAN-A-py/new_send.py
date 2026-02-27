import serial
import time

PORT = "COM6"
BAUD = 2000000  # required for USB-CAN-A UART

def checksum(data):
    return sum(data[2:]) & 0xFF

def configure_can(ser):
    set_can_baudrate = [
        0xAA, 0x55,  # header
        0x12,        # variable protocol
        0x08,        # CAN baud index: 0x08 = 100 kbps
        0x02,        # frame type: extended frame
        0x00, 0x00, 0x00, 0x00,  # filter
        0x00, 0x00, 0x00, 0x00,  # mask
        0x00,        # normal mode
        0x00,        # auto retransmit
        0x00, 0x00, 0x00, 0x00   # spare
    ]
    set_can_baudrate.append(checksum(set_can_baudrate))
    ser.write(bytes(set_can_baudrate))
    print("Config packet sent")

def send_one_frame(ser):
    frame = bytes([
        0xAA,        # header
        0xE8,        # type: extended frame, data, DLC=8
        0x67, 0x45, 0x23, 0x01,   # 29-bit ID = 0x01234567
        0x11, 0x22, 0x33, 0x44,
        0x55, 0x66, 0x77, 0x88
    ])
    ser.write(frame)
    print("Sent CAN frame: ID=0x01234567, data=11 22 33 44 55 66 77 88")

def main():
    print("Make sure Waveshare is in VARIABLE protocol, click Set + Start.")
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("Opened:", ser.portstr)

    configure_can(ser)
    time.sleep(0.1)

    while True:
        send_one_frame(ser)
        time.sleep(1)

if __name__ == "__main__":
    main()
