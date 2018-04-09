/*----------------------------------------------------------------------------
 * Description: ReWrite of NXP LPC 1785 ARM assembler XOR-decoder
 * Compile: gcc -Wall -o PktDecoder PktDecoder.c
 *----------------------------------------------------------------------------*/

/*----------------------------------------------------------------------------
 * Include Files
 *----------------------------------------------------------------------------*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/*----------------------------------------------------------------------------
 * Function argument container
 *----------------------------------------------------------------------------*/
typedef struct Ctx 
{
  uint32_t FixedSerial;
  uint16_t PCnt;
  uint16_t AvgTime;
  uint32_t PulseCnt;
  uint8_t  Power;
} Ctx;

/*----------------------------------------------------------------------------
 * Helper functions
 *----------------------------------------------------------------------------*/
uint16_t swap16(uint8_t *x)
{
  uint16_t tmp = *((uint16_t *)x);
  return ((((tmp) >> 8) & 0xffu) | (((tmp) & 0xffu) << 8)) ;
}

uint32_t swap32(uint8_t *x)
{
  uint32_t tmp = *((uint32_t *)x);
  return ((((tmp) & 0xff000000u) >> 24) | (((tmp) & 0x00ff0000u) >>  8) | (((tmp) & 0x0000ff00u) <<  8) | (((tmp) & 0x000000ffu) << 24));
}

void Copy_SPI_pktdata(uint8_t *SPI_PktData, uint8_t *localDataBuffer)
{
  memcpy(localDataBuffer, SPI_PktData, 0x18);
}

/*----------------------------------------------------------------------------
 * Decoder function
 *----------------------------------------------------------------------------*/
uint32_t XOR_function(uint8_t *SPI_PktData, Ctx *ResultCtx)
{
  size_t    i                     = 0; 
  uint8_t   localDataBuffer[18]   = { 0 };
  uint8_t   XorSeed[4]            = { 0 };
  uint8_t   XorKey[5]             = { 0 };
  uint32_t  FixedSerialOrg        = ResultCtx->FixedSerial;

  Copy_SPI_pktdata(SPI_PktData, localDataBuffer);
  uint8_t *XorData = &localDataBuffer[5];

  *((uint32_t *)XorSeed) = ResultCtx->FixedSerial + (uint32_t)0xA2C71735;

  XorKey[0] = XorSeed[3];      
  XorKey[1] = XorSeed[0];      
  XorKey[2] = XorSeed[1];
  XorKey[3] = 0x47;
  XorKey[4] = XorSeed[2];

  do
  {
    uint8_t v;
    v = *XorData ^ XorKey[i++ % 5];
    *XorData++ = v;
  } while ( i < 0xD );

  ResultCtx->FixedSerial  = swap32(&localDataBuffer[5]);
  ResultCtx->PCnt         = swap16(&localDataBuffer[9]);
  ResultCtx->AvgTime      = swap16(&localDataBuffer[11]);
  ResultCtx->PulseCnt     = swap32(&localDataBuffer[13]);
  ResultCtx->Power        = localDataBuffer[17];

  if (FixedSerialOrg != ResultCtx->FixedSerial)
  {
    ResultCtx->FixedSerial  = 0;
    ResultCtx->PCnt         = 0;
    ResultCtx->AvgTime      = 0;
    ResultCtx->PulseCnt     = 0;
    ResultCtx->Power        = 0;
  }
  return ResultCtx->FixedSerial;

}

/*----------------------------------------------------------------------------
 * Parent function feeding the decoder function with data
 *----------------------------------------------------------------------------*/
int sub_33532(void)
{
  uint8_t   SPI_PktData[18] = { 0x11, 0x49, 0x00, 0x07, 0x0f, 0xa2, 0x76, 0x17, 0x0e, 0xcf, 0xa2, 0x81, 0x48, 0x47, 0xcf, 0xa2, 0x7e, 0xd3 };
  Ctx       ctx             = { 0 };
  uint32_t  ret             = 0;

  ctx.FixedSerial = 565321;

  ret = XOR_function(SPI_PktData, &ctx);
  if (ret == 565321)
  {
    printf("FixedSerial = 0x%04x (%d)\n", ctx.FixedSerial, ctx.FixedSerial);
    printf("PCnt        = 0x%02x\n", ctx.PCnt);
    printf("AvgTime     = 0x%02x\n", ctx.AvgTime);
    printf("PulseCnt    = 0x%04x\n", ctx.PulseCnt);
    printf("Power       = 0x%01x\n", ctx.Power);
  } else {
    printf("Failed!\n");
  }

  return ret;
}

/*----------------------------------------------------------------------------
 * Test App Main
 *----------------------------------------------------------------------------*/
int main(void)
{
  sub_33532();
  return 0;
}
