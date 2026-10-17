/* Stage 4 test: OLED. Cycles through several texts so that orientation,
 * mirroring, shifts and missing lines are easy to spot.
 *
 *   2:00 (3 s) -> 60:00 (2 s) -> 8:88 (2 s) -> 1:23 (2 s) -> 9:59 (2 s)
 *
 * With FEATURE_BAR / FEATURE_BELL (plan B builds) it also erases the frame
 * clockwise and shows the bell icon.
 *
 * Wrong picture?  Rebuild with  make OLED_FLIP=0  (upside down / mirrored),
 * make OLED_COM_CFG=0x12 (every other line missing),
 * make OLED_ADDR=0x3D (blank screen). */
#include <avr/io.h>
#include <avr/pgmspace.h>
#include <util/delay.h>
#include "oled.h"

static void wait_ms(uint16_t n)
{
    while (n--)
        _delay_ms(1);
}

#if FEATURE_BAR
#define INIT_BAR() (bar_lit = BAR_PIXELS)
#else
#define INIT_BAR() ((void)0)
#endif

static void show(uint8_t a, uint8_t b, uint8_t c, uint8_t d, uint16_t ms)
{
    txt[0] = a;
    txt[1] = b;
    txt[2] = GLYPH_COLON;
    txt[3] = c;
    txt[4] = d;
    oled_draw();
    wait_ms(ms);
}

int main(void)
{
    DDRB = 1 << PB1;
    PORTB = 0;
    wait_ms(100); /* OLED power-up */
    oled_init();
    INIT_BAR();
#if FEATURE_BELL
    bell = 0;
#endif
    for (;;) {
        show(0, 2, 0, 0, 3000);
        show(6, 0, 0, 0, 2000);
        show(0, 8, 8, 8, 2000);
        show(0, 1, 2, 3, 2000);
        show(0, 9, 5, 9, 2000);
#if FEATURE_BAR
        /* the frame is erased clockwise from the top-left corner */
        for (int16_t l = BAR_PIXELS; l >= 0; l -= 4) {
            bar_lit = l;
            show(0, 2, 0, 0, 40);
        }
#endif
#if FEATURE_BELL
        bell = 1;
        show(0, 0, 0, 0, 2500);
        bell = 0;
#endif
#if FEATURE_BAR
        bar_lit = BAR_PIXELS;
#endif
    }
}
