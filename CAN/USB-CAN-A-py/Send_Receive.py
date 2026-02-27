import serial
import time

PORT = "COM6"   # change to COMx on Windows
BAUD = 2000000          # USB-CAN UART speed

def checksum(data):
    return (sum(data[2:]) & 0xFF)

def send_config(ser):
    # variable protocol, 500 kbps, STANDARD frames
    pkt = [
        0xAA, 0x55,     # header
        0x12,           # variable protocol
        0x08,           # 100 kbps
        0x01,           # standard frames
        0x00,0x00,0x00,0x00,  # filter
        0x00,0x00,0x00,0x00,  # mask
        0x00,           # normal mode
        0x00,           # auto retransmit
        0x00,0x00,0x00,0x00   # spare
    ]
    pkt.append(checksum(pkt))
    ser.write(bytes(pkt))

def send_request(ser):
    # STD frame, ID = 0x0100, DLC=8, data 10..17
    frame = bytes([
        0xAA,       # header
        0x08,       # type: std data frame, DLC = 8
        0x01, 0x00, # ID high, low -> 0x0100
        0x10, 0x11, 0x12, 0x13,
        0x14, 0x15, 0x16, 0x17,
    ])
    ser.write(frame)
    print("Sent request: ID=0x0100, data=10..17")

def read_frame(ser):
    # wait for header
    b = ser.read(1)
    if not b or b[0] != 0xAA:
        return None

    t = ser.read(1)
    if not t:
        return None
    type_len = t[0]
    dlc = type_len & 0x0F
    is_ext = bool(type_len & 0x20)

    if is_ext:
        # not expecting this in our test
        return None

    # standard ID: 2 bytes
    id_bytes = ser.read(2)
    if len(id_bytes) < 2:
        return None
    can_id = (id_bytes[0] << 8) | id_bytes[1]

    data = ser.read(dlc)
    if len(data) < dlc:
        return None

    return can_id, data

def main():
    ser = serial.Serial(PORT, BAUD)
    print("Opened", ser.portstr)

    send_config(ser)
    time.sleep(0.1)

    send_request(ser)

    print("Listening for frames...")
    while True:
        frame = read_frame(ser)
        if frame is None:
            continue
        can_id, data = frame
        if can_id == 0x100:
            print("PC->bus echo:", " ".join(f"{b:02X}" for b in data))
        elif can_id == 0x101:
            print("PP-ECU response:", " ".join(f"{b:02X}" for b in data))
        else:
            print(f"Other frame ID=0x{can_id:03X} data=",
                " ".join(f"{b:02X}" for b in data))

if __name__ == "__main__":
    main()
