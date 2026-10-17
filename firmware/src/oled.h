/* SSD1306 128x32 over bit-banged I2C, no frame buffer (64 B RAM only).
 *
 * The picture is computed on the fly and streamed column by column,
 * page by page. What is drawn is described by the globals below. */
#ifndef OLED_H
#define OLED_H

#include <stdint.h>

/* Optional (priority 3) features, selected by the Makefile. */
#ifndef FEATURE_BAR
#define FEATURE_BAR 0  /* 1 px progress frame around the screen */
#endif
#ifndef FEATURE_BELL
#define FEATURE_BELL 0 /* bell icon while the signal plays      */
#endif

/* Variables are explicitly initialised before use: .noinit avoids the
 * startup code that zeroes .bss (saves flash). */
#ifdef __AVR__
#define NOINIT __attribute__((section(".noinit")))
#else
#define NOINIT
#endif

#define BAR_PIXELS 316 /* 2*(128+32)-4: 1 px frame around the screen */

/* Glyph indices for txt[]: 0..9 = digits, GLYPH_COLON = ':' */
#define GLYPH_COLON 10

/* Text: 5 cells {m10, m1, ':', s10, s1} of glyph indices. A 0 in txt[0]
 * is not drawn (the 4 cells left are centered). */
extern uint8_t txt[5];
#if FEATURE_BAR
extern uint16_t bar_lit; /* lit pixels of the frame, 0..BAR_PIXELS    */
#endif
#if FEATURE_BELL
extern uint8_t bell;     /* non-zero: draw the bell icon              */
#endif

void oled_init(void); /* init + display on (charge pump on)         */
void oled_off(void);  /* display off + charge pump off (sleep)      */
void oled_draw(void); /* stream one whole frame (~35 ms)            */

/* Provided by oled.c (AVR) or by the host test harness. */
void oled_put(uint8_t b);

/* Provided by render.c: calls oled_put() 512 times. */
void render_frame(void);

#endif
