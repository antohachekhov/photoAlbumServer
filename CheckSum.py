
def simple_checksum(data: bytes):
    data = bytearray(data)
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum
