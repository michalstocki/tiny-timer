/* Stage 5 test: buttons. Shows  R:AAA  on the OLED:
 *   R = 1 while "run" is pressed (blank when released)
 *   AAA = ADC reading of PB4 (0..255 = 0..VCC), ladder buttons:
 *         nothing ~255, "-" ~128, "+" ~0.
 * Write the three values down; thresholds in timebase.h are <64 "+",
 * 64..191 "-", >=192 nothing. */
#include <avr/io.h>
#include <util/delay.h>
#include "oled.h"

static void wait_ms(uint16_t n)
{
    while (n--)
        _delay_ms(1);
}

int main(void)
{
    DDRB = 1 << PB1;
    PORTB = 1 << PB3;
    ADMUX = (1 << ADLAR) | 2;
    ADCSRA = (1 << ADEN) | (1 << ADSC) | (1 << ADATE) | 7;
    wait_ms(100);
    oled_init();
    for (;;) {
        uint8_t a = ADCH;
        txt[0] = !(PINB & (1 << PB3));
        txt[1] = GLYPH_COLON;
        txt[2] = a / 100;
        txt[3] = (a / 10) % 10;
        txt[4] = a % 10;
        oled_draw();
        wait_ms(100);
    }
}
