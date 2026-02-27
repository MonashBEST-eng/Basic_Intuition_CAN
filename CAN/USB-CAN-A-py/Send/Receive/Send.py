import serial
import time

# Open serial port to Waveshare
t = serial.Serial("COM6", 115200)
print("Opened:", t.portstr)

def calculate_checksum(data):
    checksum = sum(data[2:])
    return checksum & 0xff

# --- Configure CAN: 100 kbps, STANDARD frames ---
set_can_baudrate = [
    0xaa,     # 0  Packet header
    0x55,     # 1  Packet header
    0x12,     # 2  Type: variable protocol
    0x08,     # 3  CAN Baud Rate: 0x08 = 100 kbps
    0x01,     # 4  Frame Type: 0x01 = STANDARD frame (important!)
    0x00,     # 5  Filter ID1
    0x00,     # 6  Filter ID2
    0x00,     # 7  Filter ID3
    0x00,     # 8  Filter ID4
    0x00,     # 9  Mask ID1
    0x00,     # 10 Mask ID2
    0x00,     # 11 Mask ID3
    0x00,     # 12 Mask ID4
    0x00,     # 13 CAN mode: 0x00 = normal
    0x00,     # 14 automatic resend
    0x00,     # 15 Spare
    0x00,     # 16 Spare
    0x00,     # 17 Spare
    0x00,     # 18 Spare
]

checksum = calculate_checksum(set_can_baudrate)
set_can_baudrate.append(checksum)
set_can_baudrate = bytes(set_can_baudrate)

num_set_baud = t.write(set_can_baudrate)
print(f"Set CAN baud cmd sent, bytes written: {num_set_baud}")

time.sleep(0.5)

# ---- Build a STANDARD data frame: ID = 0x100, DLC = 8, data = "PINGPING" ----

can_id = 0x100
data_bytes = b"PINGPING"  # exactly 8 bytes

# Header byte 1: 0xAA (sync)
# Header byte 2:
#   bits7-6: 11 (0xC0)           -> frame indicator
#   bit5:    0  (standard frame)
#   bit4:    0  (data frame, not remote)
#   bits3-0: DLC = 8 (0x8)
second_byte = 0xC0 | 0x08       # = 0xC8

id_low  = can_id & 0xFF         # low byte
id_high = (can_id >> 8) & 0xFF  # high byte

frame = bytearray()
frame.append(0xAA)              # header
frame.append(second_byte)       # type + dlc
frame.append(id_low)            # ID low
frame.append(id_high)           # ID high

# Add data, pad to 8 if needed
frame.extend(data_bytes)
while len(frame) < 2 + 2 + 8:   # header(2) + id(2) + 8 data
    frame.append(0x00)

frame.append(0x55)              # end byte

print("Sending CAN frame bytes:", frame)
n = t.write(frame)
print("Bytes written:", n)

t.close()
