/* Bit-banged I2C master + SSD1306 128x32 driver (write only, ACK ignored).
 * Open drain: line low = pin as output driving 0, line high = pin as input
 * (pull-ups are on the OLED module). PORTB bits of SDA/SCL stay 0. */
#include <avr/io.h>
#include <avr/pgmspace.h>
#include "oled.h"

#define SDA (1 << PB0)
#define SCL (1 << PB2)
#ifndef OLED_ADDR
#define OLED_ADDR 0x3C    /* 7-bit address; 0x3D if the module is strapped so */
#endif
#ifndef OLED_FLIP
#define OLED_FLIP 1       /* 1 = rotate the picture 180 degrees (A1/C8), 0 = A0/C0 */
#endif
#ifndef OLED_COM_CFG
#define OLED_COM_CFG 0x02 /* COM pins config: 0x02 for most 128x32, 0x12 if every other line is missing */
#endif

#define SDA_LO() (DDRB |= SDA)
#define SDA_HI() (DDRB &= ~SDA)
#define SCL_LO() (DDRB |= SCL)
#define SCL_HI() (DDRB &= ~SCL)
/* Delays (0.104 us per cycle at 9.6 MHz). The bus runs at about 250 kHz:
 * inside the SSD1306 limit (400 kHz) and slow enough for 10k pull-ups on a
 * breadboard (rise time ~1 us). */
#ifdef __AVR__
#define NOPS2() __asm__ volatile("rjmp .+0\n\trjmp .+0" ::: "memory") /* 4 cycles */
#define LOOPDLY(n) /* 3*n cycles, 3 words */                                  \
    do {                                                                       \
        uint8_t d_;                                                            \
        __asm__ volatile("ldi %0, %1\n1: dec %0\n\tbrne 1b" : "=d"(d_) : "M"(n)); \
    } while (0)
#else /* host simulation */
#define NOPS2() ((void)0)
#define LOOPDLY(n) ((void)0)
#endif

static void i2c_start(void)
{
    SDA_HI();
    SCL_HI();
    NOPS2();
    SDA_LO(); /* START: SDA falls while SCL high */
    NOPS2();
    SCL_LO();
}

static void i2c_stop(void)
{
    SDA_LO();
    SCL_HI();
    NOPS2();
    SDA_HI(); /* STOP: SDA rises while SCL high */
}

/* 8 data bits + a 9th "1" (SDA released) for the ACK slot. */
void oled_put(uint8_t b)
{
    uint16_t w = ((uint16_t)b << 8) | 0x80;
    uint8_t n = 9;
    do {
        if (w & 0x8000)
            SDA_HI();
        else
            SDA_LO();
        w <<= 1;
        LOOPDLY(4); /* data setup; SCL low ~1.9 us in total */
        SCL_HI();
        LOOPDLY(6); /* SCL high ~1.9 us */
        SCL_LO();
    } while (--n);
}

static void begin(uint8_t control) /* 0x00 = commands, 0x40 = data */
{
    i2c_start();
    oled_put(OLED_ADDR << 1);
    oled_put(control);
}

/* Command bytes sent by oled_init() (after the 0x00 control byte). */
static const uint8_t init_cmds[] PROGMEM = {
    0xA8, 0x1F,       /* multiplex ratio: 32 rows                       */
    0x8D, 0x14,       /* charge pump on                                 */
    0x20, 0x01,       /* vertical addressing mode (stream is per column) */
    0x22, 0x00, 0x03, /* page range 0..3; column range stays 0..127.    */
    0xDA, OLED_COM_CFG, /* COM pins hardware configuration              */
    0xA0 | OLED_FLIP, 0xC0 | (OLED_FLIP << 3), /* segment remap, COM scan direction */
    0xAF,             /* display on                                     */
};

static void cmd_stream(const uint8_t *p, uint8_t n)
{
    begin(0x00);
    while (n--)
        oled_put(pgm_read_byte(p++));
    i2c_stop();
}

void oled_init(void)
{
    cmd_stream(init_cmds, sizeof init_cmds);
}

static const uint8_t off_cmds[] PROGMEM = {0xAE, 0x8D, 0x10};

void oled_off(void)
{
    cmd_stream(off_cmds, sizeof off_cmds);
}

void oled_draw(void)
{
    /* A full frame is exactly 512 bytes, after which the write pointer
     * wraps to column 0 / page 0, so no address commands are needed. */
    begin(0x40);
    render_frame();
    i2c_stop();
}
