import serial
import time

strFrameType = ""
strFrameFormat = ""
len2 = 0
id = 0

print(
    "The converter is equipped with two built-in conversion protocols,\n"
    "one is a fixed 20 byte protocol and the other is a variable length protocol.\n"
    "This script uses the variable length protocol.\n"
)

ser = serial.Serial("COM6", 115200)
print("Opened:", ser.portstr)

def calculate_checksum(data):
    checksum = sum(data[2:])
    return checksum & 0xff

# --- Configure CAN: 100 kbps, STANDARD frames ---
set_can_baudrate = [
    0xaa,     # 0  Packet header
    0x55,     # 1  Packet header
    0x12,     # 2  Type: variable protocol
    0x08,     # 3  CAN Baud Rate: 100 kbps
    0x01,     # 4  Frame Type: 0x01 = STANDARD frame (important!)
    0x00,     # 5  Filter ID1
    0x00,     # 6  Filter ID2
    0x00,     # 7  Filter ID3
    0x00,     # 8  Filter ID4
    0x00,     # 9  Mask ID1
    0x00,     # 10 Mask ID2
    0x00,     # 11 Mask ID3
    0x00,     # 12 Mask ID4
    0x00,     # 13 CAN mode: normal
    0x00,     # 14 automatic resend
    0x00,     # 15 Spare
    0x00,     # 16 Spare
    0x00,     # 17 Spare
    0x00,     # 18 Spare
]

checksum = calculate_checksum(set_can_baudrate)
set_can_baudrate.append(checksum)
set_can_baudrate = bytes(set_can_baudrate)

ser.write(set_can_baudrate)
print("CAN baud rate setting command sent.\nListening for frames...")

while True:
    # Read first 2 bytes (header)
    data = ser.read(2)
    if not data or len(data) < 2:
        continue

    hex_data1 = [hex(byte) for byte in data]

    if (data[0] == 0xaa) and (data[1] & 0xC0 == 0xC0):  # frame header
        dlc = data[1] & 0x0F

        if data[1] & 0x10 == 0x00:
            strFrameFormat = "Data Frame"
        else:
            strFrameFormat = "Remote Frame"

        if data[1] & 0x20 == 0x00:
            strFrameType = "Standard Frame"
            len2 = dlc + 3  # 2 bytes ID + dlc + end
        else:
            strFrameType = "Extended Frame"
            len2 = dlc + 5  # 4 bytes ID + dlc + end

        data2 = ser.read(len2)
        if len(data2) < len2:
            continue

        hex_data = [hex(byte) for byte in data2]
        hex_data1 += hex_data
        print("Raw bytes:", hex_data1)

        if data2[len2 - 1] == 0x55:  # end code
            if strFrameType == "Standard Frame":
                id_val = data2[1]
                id_val <<= 8
                id_val += data2[0]
                strId = hex(id_val)

                if dlc > 0:
                    CanData = hex_data[2:2 + dlc]
                else:
                    CanData = ["No Data"]
            else:
                id_val = data2[3]
                id_val <<= 8
                id_val += data2[2]
                id_val <<= 8
                id_val += data2[1]
                id_val <<= 8
                id_val += data2[0]
                strId = hex(id_val)
                if dlc > 0:
                    CanData = hex_data[4:4 + dlc]
                else:
                    CanData = ["No Data"]

            print("Receive CAN id:", strId, "Data:", CanData)
            print(strFrameType + ", " + strFrameFormat)

            # Try decode ASCII
            if CanData != ["No Data"]:
                try:
                    byte_vals = [int(x, 16) for x in CanData]
                    ascii_chunk = bytes(byte_vals).decode("ascii", errors="ignore")
                    print("ASCII chunk:", repr(ascii_chunk))
                except Exception as e:
                    print("ASCII decode error:", e)

            # Special note when we see reply from pp-ECU
            if strFrameType == "Standard Frame" and id_val == 0x101:
                print("✅ Got reply from pp-ECU (ID 0x101)")

        else:
            print("Receive Packet header Error")

    time.sleep(0.1)
