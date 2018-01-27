#=============================================================================
# Ikea Sparsnas packet decoder using Yard Stick One along with RfCat
#=============================================================================
import os
import sys
import binascii
from datetime import datetime
from time import localtime, strftime
from rflib import *

#-----------------------------------------------------------------------------
#------------------------------ Global variables -----------------------------
#-----------------------------------------------------------------------------
d = RfCat()
XOR_KEY = [0x47, 0xcf, 0xa2, 0x7e, 0xb7] # Xor-key for sensor "400 565 321"

#-----------------------------------------------------------------------------
# Initialize radio
#-----------------------------------------------------------------------------
def init(d):
    d.setFreq(868000000)            # Main frequency
    d.setMdmModulation(MOD_2FSK)    # Modulation type
    d.setMdmChanSpc(40000)          # Channel spacing
    d.setMdmDeviatn(20000)          # Deviation
    d.setMdmNumPreamble(32)         # Number of preamble bits
    d.setMdmDRate(38391)            # Data rate
    d.setMdmSyncWord(0xD201)        # Sync Word
    d.setMdmSyncMode(1)             # 15 of 16 bits must match
    d.makePktFLEN(20)               # Packet length
    d.setMaxPower()

#-----------------------------------------------------------------------------
# Crc16 helper
#-----------------------------------------------------------------------------
def culCalcCRC(crcData, crcReg):
    CRC_POLY = 0x8005
    
    for i in xrange(0,8):
        if ((((crcReg & 0x8000) >> 8) ^ (crcData & 0x80)) & 0XFFFF) :
            crcReg = (((crcReg << 1) & 0XFFFF) ^ CRC_POLY ) & 0xFFFF
        else:
            crcReg = (crcReg << 1) & 0xFFFF
        crcData = (crcData << 1) & 0xFF
    return crcReg

#-----------------------------------------------------------------------------
# crc16
#-----------------------------------------------------------------------------
def crc16(txtBuffer, expectedChksum):
    CRC_INIT = 0xFFFF
    checksum = CRC_INIT

    hexarray = bytearray.fromhex(txtBuffer)
    for i in hexarray:
        checksum = culCalcCRC(i, checksum)

    if checksum == int(expectedChksum, 16):
        #print "(CRC OK)"
        return True
    else:
        #print "(CRC FAIL) Expected=" + expectedChksum + " Calculated=" + str(hex(checksum))
        return False

#-----------------------------------------------------------------------------
# "main"
#-----------------------------------------------------------------------------
print "Initialize modem..."
init(d)

print "Waiting for packet..."
print ""
print "Len ID Cnt Status Fixed    PCnt Watt PulseCnt ?? Crc16"
print "--- -- --- ------ -----    ---- ---- -------- -- -----"

#-----------------
# Read packet loop
#-----------------
while True:
    capture = ""
    
    #---------------------------------
    # Wait for a packet to be captured
    #---------------------------------
    try:
        y,z = d.RFrecv()
        capture = y.encode('hex')
        #print capture

    except ChipconUsbTimeoutException:
        pass

    #------------------------
    # When we get a packet...
    #------------------------
    if capture:

        # Extract packet content to the formal TexasInstruments packet layout
        pkt_length  = capture[0:0+2]
        pkt_address = capture[2:2+2]
        pkt_data    = ""
        for x in xrange(4, len(capture) - 4, 2):
            currElement = capture[x:x+2]
            pkt_data += currElement + " "
        pkt_crc     = capture[36:36+2] + " " + capture[38:38+2]

        # Verify crc16 accordingly to the TexasInstruments implementation
        crcBuf_str  = (pkt_length + pkt_address + pkt_data).replace(" ","")
        expectedCrc = capture[36:36+2] + capture[38:38+2]
        crcOk       = crc16(crcBuf_str, expectedCrc)

        if crcOk == False:
            #print "Crc NOK"
            continue

        if crcOk:

            xorkey           = bytearray(XOR_KEY)
            xorkeyarray      = bytearray([0, 0, 0]) + xorkey + xorkey + xorkey + bytearray([0, 0]) 
            hexarray         = bytearray.fromhex(capture.replace(" ",""))
            hexarray_decoded = bytearray()
            
            # Unscramble
            for i in xrange(0, len(xorkeyarray)):
                hexarray_decoded.append(hexarray[i] ^ xorkeyarray[i])

            Len, ID, Cnt, Status, Fixed, PCnt, AvgTimeBetweenPulses, PulseCnt, Unknown, Crc = struct.unpack('>BBBHIHHIBH', hexarray_decoded)
            print str.format(' {:02X}', Len),
            print str.format('{:02X}', ID),
            print str.format('{:02X} ', Cnt),
            print str.format('{:04X}  ', Status),
            print str.format('{:08X}', Fixed),
            print str.format('{:04X}', PCnt),
            print str.format('{:04X}', AvgTimeBetweenPulses),
            print str.format('{:08X}', PulseCnt),
            print str.format('{:02X}', Unknown),
            print str.format('{:04X}', Crc),

            Watt = (3686400 / AvgTimeBetweenPulses)
            print " # Current power = " + str(Watt)
