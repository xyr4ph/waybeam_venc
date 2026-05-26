#!/usr/bin/env python3
import socket
import struct
import signal
import sys

LISTEN = ("0.0.0.0", 5600)
FORWARD = ("127.0.0.1", 5601)
PROFILE_ID = 0xABAC

def main():
    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.bind(LISTEN)
    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def shutdown(*_):
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        data, addr = rx.recvfrom(2048)
        if len(data) < 12:
            continue

        byte0 = data[0]
        version = (byte0 >> 6) & 0x03
        if version != 2:
            continue

        extension_bit = (byte0 >> 4) & 0x01
        cc = byte0 & 0x0F
        sequence_number = struct.unpack(">H", data[2:4])[0]
        rtp_timestamp = struct.unpack(">I", data[4:8])[0]

        offset = 12 + cc * 4

        if extension_bit and len(data) >= offset + 4:
            profile_id = struct.unpack(">H", data[offset:offset+2])[0]

            # Length of the extension header in bytes, multiplied by 4 as it comes in 32-bit words
            ext_header_len = struct.unpack(">H", data[offset+2:offset+4])[0] * 4

            # ext_header_len must be 8 as we sent a 64-bit timestamp
            if profile_id == PROFILE_ID and ext_header_len == 8 and len(data) >= offset + 4 + ext_header_len:
                utc_timestamp = struct.unpack(">Q", data[offset+4:offset+12])[0]

                print(f"[EXT] seq={sequence_number} rtp_ts={rtp_timestamp} abs_ts_us={utc_timestamp}")

            offset += 4 + ext_header_len

        # Strip extension and CSRCs, rebuild clean 12-byte header
        if extension_bit or cc:
            clean = bytearray(12)
            clean[0] = 0x80                      # V=2, P=0, X=0, CC=0
            clean[1] = data[1]                   # preserve marker + payload type
            clean[2:4] = struct.pack(">H", sequence_number)
            clean[4:8] = struct.pack(">I", rtp_timestamp)
            clean[8:12] = data[8:12]             # SSRC
            payload = bytes(clean) + data[offset:]
        else:
            payload = data

        tx.sendto(payload, FORWARD)

if __name__ == "__main__":
    main()