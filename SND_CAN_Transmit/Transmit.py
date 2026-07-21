"""Slow CAN request/response handshake.

PC/Waveshare side:
  1. Sends ID 0x123 with a 32-bit counter.
  2. Waits for STM32 response on ID 0x124.
  3. Verifies that the returned payload matches.
  4. Prints ACKNOWLEDGED.
  5. Repeats once per second.
"""

from __future__ import annotations

import time
import can

BITRATE = 500_000
REQUEST_ID = 0x123
RESPONSE_ID = 0x124
PERIOD_SECONDS = 1.0
RESPONSE_TIMEOUT_SECONDS = 0.75

# Change these two values for your adapter.
# PEAK PCAN example:
INTERFACE = "pcan"
CHANNEL = "PCAN_USBBUS1"

# Typical serial/SLCAN example:
# INTERFACE = "slcan"
# CHANNEL = "COM6"


def counter_payload(counter: int) -> bytes:
    return counter.to_bytes(4, byteorder="big", signed=False)


def main() -> None:
    print(f"Opening {INTERFACE}:{CHANNEL} at {BITRATE // 1000} kbit/s...")

    try:
        bus = can.Bus(
            interface=INTERFACE,
            channel=CHANNEL,
            bitrate=BITRATE,
        )
    except Exception as exc:
        raise SystemExit(f"Could not open CAN adapter: {exc}") from exc

    counter = 0

    print(
        f"Sending ID 0x{REQUEST_ID:03X}; "
        f"waiting for ID 0x{RESPONSE_ID:03X}."
    )
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            cycle_start = time.monotonic()
            payload = counter_payload(counter)

            request = can.Message(
                arbitration_id=REQUEST_ID,
                is_extended_id=False,
                data=payload,
            )

            try:
                bus.send(request, timeout=0.5)
            except can.CanError as exc:
                print(f"TX FAILED | counter={counter} | {exc}")
            else:
                print(
                    f"TX | ID=0x{REQUEST_ID:03X} | "
                    f"Counter={counter} | Data={payload.hex(' ').upper()}"
                )

                deadline = time.monotonic() + RESPONSE_TIMEOUT_SECONDS
                acknowledged = False

                while time.monotonic() < deadline:
                    remaining = deadline - time.monotonic()
                    message = bus.recv(timeout=max(0.0, remaining))

                    if message is None:
                        break

                    if message.is_error_frame:
                        print(
                            "CAN ERROR FRAME | "
                            f"Data={bytes(message.data).hex(' ').upper()}"
                        )
                        continue

                    if (
                        not message.is_extended_id
                        and message.arbitration_id == RESPONSE_ID
                    ):
                        response_data = bytes(message.data)

                        print(
                            f"RX | ID=0x{RESPONSE_ID:03X} | "
                            f"DLC={message.dlc} | "
                            f"Data={response_data.hex(' ').upper()}"
                        )

                        if response_data == payload:
                            print("ACKNOWLEDGED: response payload verified\n")
                        else:
                            print("RESPONSE RECEIVED, BUT PAYLOAD DID NOT MATCH\n")

                        acknowledged = True
                        break

                if not acknowledged:
                    print("NO ACKNOWLEDGEMENT: response timeout\n")

            counter = (counter + 1) & 0xFFFFFFFF

            elapsed = time.monotonic() - cycle_start
            time.sleep(max(0.0, PERIOD_SECONDS - elapsed))

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        bus.shutdown()


if __name__ == "__main__":
    main()
