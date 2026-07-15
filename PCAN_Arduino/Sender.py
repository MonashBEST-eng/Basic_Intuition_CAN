import time
import can

PCAN_CHANNEL = "PCAN_USBBUS1"
CAN_BITRATE = 500_000

TX_CAN_ID = 0x100
SEND_INTERVAL_SECONDS = 2.0


def main() -> None:
    bus = None
    counter = 0
    last_send_time = time.monotonic()

    try:
        print("Connecting to PCAN-USB...")

        bus = can.Bus(
            interface="pcan",
            channel=PCAN_CHANNEL,
            bitrate=CAN_BITRATE,
        )

        print("Connected.")
        print(
            f"Sending CAN ID 0x{TX_CAN_ID:03X} "
            f"every {SEND_INTERVAL_SECONDS:.0f} seconds."
        )
        print("Listening for incoming CAN frames.")
        print("Press Ctrl+C to stop.\n")

        while True:
            current_time = time.monotonic()

            # Send one frame every two seconds, matching the STM32 code.
            if current_time - last_send_time >= SEND_INTERVAL_SECONDS:
                last_send_time = current_time

                # Convert the counter into four bytes, most-significant byte first.
                data = [
                    (counter >> 24) & 0xFF,
                    (counter >> 16) & 0xFF,
                    (counter >> 8) & 0xFF,
                    counter & 0xFF,
                ]

                message = can.Message(
                    arbitration_id=TX_CAN_ID,
                    is_extended_id=False,
                    is_remote_frame=False,
                    data=data,
                )

                try:
                    bus.send(message, timeout=1.0)

                    print(
                        f"TX -> ID=0x{TX_CAN_ID:X}  "
                        f"Counter={counter}"
                    )

                    counter = (counter + 1) & 0xFFFFFFFF

                except can.CanError as error:
                    print(f"CAN transmission failed: {error}")

            # Check for received messages without blocking for too long.
            received_message = bus.recv(timeout=0.05)

            if received_message is not None:
                raw_data = " ".join(
                    f"{byte:02X}" for byte in received_message.data
                )

                # Interpret the first four bytes as a big-endian counter,
                # matching the STM32 program.
                if received_message.dlc >= 4:
                    received_counter = int.from_bytes(
                        received_message.data[:4],
                        byteorder="big",
                        signed=False,
                    )

                    counter_text = f"Counter={received_counter}  "
                else:
                    counter_text = ""

                print(
                    f"CAN RX: ID=0x{received_message.arbitration_id:X}  "
                    f"DLC={received_message.dlc}  "
                    f"{counter_text}"
                    f"RawData: {raw_data}"
                )

    except KeyboardInterrupt:
        print("\nProgram stopped.")

    except Exception as error:
        print(f"PCAN error: {error}")

    finally:
        if bus is not None:
            bus.shutdown()
            print("PCAN connection closed.")


if __name__ == "__main__":
    main()