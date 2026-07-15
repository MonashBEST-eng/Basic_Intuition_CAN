import time
import can

PCAN_CHANNEL = "PCAN_USBBUS1"
CAN_BITRATE = 500_000

REQUEST_ID = 0x123
RESPONSE_ID = 0x124

RESPONSE_TIMEOUT_SECONDS = 2.0
DELAY_BETWEEN_REQUESTS_SECONDS = 1.0


def format_data(data: bytes | bytearray) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def main() -> None:
    bus = None
    counter = 0

    try:
        print("Connecting to PCAN-USB...")

        bus = can.Bus(
            interface="pcan",
            channel=PCAN_CHANNEL,
            bitrate=CAN_BITRATE,
        )

        print("Connected at 500 kbit/s.")
        print(f"Request ID:  0x{REQUEST_ID:03X}")
        print(f"Response ID: 0x{RESPONSE_ID:03X}")
        print("Press Ctrl+C to stop.\n")

        while True:
            request_data = counter.to_bytes(
                length=4,
                byteorder="big",
                signed=False,
            )

            request = can.Message(
                arbitration_id=REQUEST_ID,
                is_extended_id=False,
                is_remote_frame=False,
                data=request_data,
            )

            try:
                bus.send(request, timeout=1.0)

                print(
                    f"PCAN TX | ID=0x{REQUEST_ID:03X} | "
                    f"Counter={counter} | "
                    f"Data={format_data(request_data)}"
                )

            except can.CanError as error:
                print(f"PCAN transmission failed: {error}")
                time.sleep(1.0)
                continue

            response_received = False
            response_deadline = time.monotonic() + RESPONSE_TIMEOUT_SECONDS

            while time.monotonic() < response_deadline:
                remaining_time = response_deadline - time.monotonic()

                response = bus.recv(
                    timeout=max(0.0, min(remaining_time, 0.1))
                )

                if response is None:
                    continue

                # Ignore local transmit echoes and unrelated CAN traffic.
                if response.arbitration_id != RESPONSE_ID:
                    continue

                received_data = bytes(response.data)

                print(
                    f"PCAN RX | ID=0x{response.arbitration_id:03X} | "
                    f"DLC={response.dlc} | "
                    f"Data={format_data(received_data)}"
                )

                if received_data == request_data:
                    print("Reply verified: PASS\n")
                else:
                    print(
                        "Reply verified: FAIL "
                        f"(expected {format_data(request_data)})\n"
                    )

                response_received = True
                break

            if not response_received:
                print("Timed out waiting for the H7 response.\n")

            counter = (counter + 1) & 0xFFFFFFFF
            time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

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