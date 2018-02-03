#=============================================================================
# Ikea Sparsnas packet decoder using Yard Stick One along with RfCat.
# This version dumps the packets 'as is' (e.g.'raw'). It uses colors to visualize 
# any changes between the current packet and previously sent packets. This is
# helpful when looking for patterns in the data.
#=============================================================================
import os
import sys
from datetime import datetime
from time import localtime, strftime
from rflib import *

#-----------------------------------------------------------------------------
#------------------------------ Global variables -----------------------------
#-----------------------------------------------------------------------------
logfilename = ""
Verbose     = False
Hdr         = True
d           = RfCat()

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
localtime_now       = localtime()
localtime_last      = localtime()
localtime_now_str   = strftime("%Y-%m-%d %H:%M:%S", localtime_now)
localtime_last_str  =  strftime("%Y-%m-%d %H:%M:%S", localtime_last)
logrow_last         = "-------------------------------------------------------------------------------------------"
RED                 = "\033[1;31;40m"
GREEN               = "\033[1;32;40m"
YELLOW              = "\033[1;33;40m"

if len(sys.argv) > 1:
    logfilename = sys.argv[1]

print "Initialize modem..."
init(d)

print "Waiting for packet..."
#d.RFlisten()


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
    # When we got a packet...
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

        if Verbose:
            print "pkt.length        = " + pkt_length
            print "pkt.address_field = " + pkt_address
            print "pkt.data_field    = " + pkt_data
            print "pkt.crc16         = " + pkt_crc + " (CRC verification: " + str(crcOk) + ")"
            print ""
        else:
            if crcOk:
                if Hdr:
                    print "Timestamp            Len ID Nr Stat Fixed    Nr2  Data Cnt3       Crc16"
                    print "--------------------- -- -- -- ---- -------- ---- ---- ---------- ----"
                    Hdr = False

                # Ugly hack to keep track of missing packets
                localtime_now       = localtime()
                localtime_now_str   = strftime("%Y-%m-%d %H:%M:%S", localtime_now)
                d1 = datetime.strptime(localtime_now_str, "%Y-%m-%d %H:%M:%S")
                d2 = datetime.strptime(localtime_last_str, "%Y-%m-%d %H:%M:%S")
                timediff = (d1 - d2).total_seconds()
                if (timediff > 20.0):
                    print YELLOW + "*** Packets missing ***"
                localtime_last     = localtime_now
                localtime_last_str = localtime_now_str

                # Format the line we're going to print
                timestamp   = strftime("%Y-%m-%d %H:%M:%S", localtime_now)
                pkt_data = pkt_data.replace(" ","")
                pkt_data2 = ""
                spacelist = [2, 6, 14, 18, 22, 30]
                for x in range(len(pkt_data)):
                    if x in spacelist:
                        pkt_data2 += " "
                    pkt_data2 += pkt_data[x]
                logrow = "[" + timestamp + "] " + pkt_length + " " + pkt_address + " " + pkt_data2 + " " + pkt_crc.replace(" ","")
                
                # Print the line, and while doing so, compare each character to the characters
                # in the previously seen packet. Highlight any changes in Red color.                
                for i in range(min(len(logrow), len(logrow_last))):
                    if logrow[i] != logrow_last[i]:
                        sys.stdout.write(RED + logrow[i])
                    else:
                        sys.stdout.write(GREEN + logrow[i])
                print ""

                # Optionally, save our line to a textfile log
                if len(logfilename) > 0:
                    with open(logfilename, 'a') as f:
                        f.write(logrow)
                        f.write("\n")
                        f.flush()
                logrow_last = logrow