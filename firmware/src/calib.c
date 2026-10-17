/* Stage 8: time calibration (OSCCAL) of the internal RC oscillator.
 *
 * Ready screen shows the current OSCCAL value as  :NNN  (the factory value
 * after reset). "+" / "-" change OSCCAL by 1 and apply it at once.
 * "run" starts a count-UP from 0:00 using the same time base as the real
 * timer; at CAL_MIN:00 it beeps for 1 s and returns to the ready screen.
 * Start a phone stopwatch at the moment you release "run", stop it at the
 * beep:  phone time > CAL_MIN min  => device is slow => raise OSCCAL.
 * "run" again during the count aborts. */
#include "oled.h"
#include "timebase.h"

#ifndef CAL_MIN
#define CAL_MIN 10 /* length of one calibration run, minutes (1..59) */
#endif
#ifndef TONE_HZ
#define TONE_HZ 2000
#endif

static void show_osc(void)
{
    uint8_t v = OSCCAL;
    txt[0] = 0;
    txt[1] = GLYPH_COLON;
    txt[2] = v / 100;
    txt[3] = (v / 10) % 10;
    txt[4] = v % 10;
    oled_draw();
}

static void inc(void) /* count up by one second, digits m10 m1 : s10 s1 */
{
    uint8_t i = 4;
    for (;;) {
        if (txt[i] < ((i == 3) ? 5 : 9)) {
            txt[i]++;
            return;
        }
        txt[i] = 0;
        i = (i == 3) ? 1 : i - 1;
    }
}

static void beep(void)
{
    TIMSK0 = 0;
    OCR0A = TONE_TOP(TONE_HZ);
    TCNT0 = 0;
    TCCR0B = CS_TONE;
    TCCR0A = (1 << COM0B0) | (1 << WGM01);
    delay_ms(1000);
    timer_tick();
}

int main(void)
{
    uint8_t e;

    hw_init();
    delay_ms(100);
    oled_init();
    show_osc();
    for (;;) {
        wait_event();
        e = ev;
        ev = 0;
        if (e == B_RUN) {
            if (running) {
                running = 0;
                show_osc();
            } else {
                running = 1;
                txt[0] = txt[1] = txt[3] = txt[4] = 0;
                txt[2] = GLYPH_COLON;
                oled_draw();
                cli();
                TCNT0 = 0;
                tick = 0;
                seen = secs;
                sei();
            }
        } else if (e == B_PLUS || e == B_MINUS) {
            if (!running) {
                uint8_t v = OSCCAL;
                if (e == B_PLUS && v < 127)
                    OSCCAL = v + 1;
                else if (e == B_MINUS && v > 0)
                    OSCCAL = v - 1;
                show_osc();
            }
        } else if (!e) {                /* one more second elapsed */
            seen++;
            inc();
            oled_draw();
            if (txt[0] == CAL_MIN / 10 && txt[1] == CAL_MIN % 10 &&
                !txt[3] && !txt[4]) {
                beep();
                running = 0;
                show_osc();
                ev = 0;
            }
        }
    }
}
