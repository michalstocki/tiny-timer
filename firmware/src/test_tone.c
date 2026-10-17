/* Stage 3 test: speaker. No display needed.
 *
 *   default:  plays 500, 1000, 1500, 2000, 2500, 3000, 4000 Hz, 0.5 s each
 *             with 0.5 s pauses, then 3 s of silence, and repeats.
 *   HEAT_TEST (make heat FREQ=2000): one continuous tone of FREQ_HZ for 20 s
 *             (check that the transistor and the resistor stay cool), then
 *             silence.
 *
 * Tone = Timer0 CTC, OC0B (PB1) toggles every OCR0A+1 counts of clk/64:
 * f = F_CPU / 128 / (OCR0A + 1)  (9.6 MHz: 75000 / (OCR0A + 1)). */
#include <avr/io.h>
#include <avr/pgmspace.h>
#include <util/delay.h>

#define TONE_TOP(hz) ((uint8_t)((F_CPU / 128 + (hz) / 2) / (hz) - 1))

static void tone(uint8_t top)
{
    OCR0A = top;
    TCNT0 = 0;
    TCCR0A = (1 << COM0B0) | (1 << WGM01);
    TCCR0B = (1 << CS01) | (1 << CS00); /* clk/64 */
}

static void silence(void)
{
    TCCR0A = 1 << WGM01; /* OC0B disconnected, PB1 = 0 */
}

static void wait_ms(uint16_t n)
{
    while (n--)
        _delay_ms(1);
}

int main(void)
{
    DDRB = 1 << PB1; /* speaker transistor base resistor on PB1, low */
    PORTB = 0;
#ifdef HEAT_TEST
    tone(TONE_TOP(FREQ_HZ));
    wait_ms(20000);
    silence();
    for (;;)
        ;
#else
    static const uint8_t tops[] PROGMEM = {
        TONE_TOP(500),  TONE_TOP(1000), TONE_TOP(1500), TONE_TOP(2000),
        TONE_TOP(2500), TONE_TOP(3000), TONE_TOP(4000),
    };
    for (;;) {
        for (uint8_t i = 0; i < sizeof tops; i++) {
            tone(pgm_read_byte(&tops[i]));
            wait_ms(500);
            silence();
            wait_ms(500);
        }
        wait_ms(3000);
    }
#endif
}
