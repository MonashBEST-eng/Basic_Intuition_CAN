import can

bus = can.interface.Bus(
    interface="pcan",
    channel="PCAN_USBBUS1",
    bitrate=125000
)

print("PCAN receiver started. Waiting for frames...")

while True:
    msg = bus.recv(timeout=1.0)

    if msg is None:
        print("No frame")
        continue

    print(
        f"ID: 0x{msg.arbitration_id:X} "
        f"DLC: {msg.dlc} "
        f"DATA: {msg.data.hex(' ').upper()}"
    )