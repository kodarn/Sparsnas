import sys

def culCalcCRC(crcData, crcReg):
    CRC_POLY = 0x8005

    for i in xrange(0, 8):
        if ((((crcReg & 0x8000) >> 8) ^ (crcData & 0x80)) & 0xFFFF):
            crcReg = (((crcReg << 1) & 0xFFFF) ^ CRC_POLY) & 0xFFFF
        else:
            crcReg = (crcReg << 1) & 0xFFFF
        crcData = (crcData << 1) & 0xFF
    
    return crcReg

def crc16(txtBuffer, expectedChksum):
    CRC_INIT = 0xFFFF
    checksum = CRC_INIT

    hexarray = bytearray.fromhex(txtBuffer)
    for i in hexarray:
        checksum = culCalcCRC(i, checksum)

    if checksum == int(expectedChksum, 16):
        print "CRC OK"
        return True
    else:
        print "CRC Fail. Expected=" + expectedChksum + " Calculated=" + str(hex(checksum))
        return False

#
# Main
#
payload = "11431d070ea270e904cfbf737e47cfa334e0"
expectedCrc = "1204"
success = crc16(payload, expectedCrc)
print "Match" + success
