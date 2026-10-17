/* Tiny timer, ATtiny13A @ 9.6 MHz (CKDIV8 off).
 *
 *   PB0 SDA   PB1 speaker (OC0B)   PB2 SCL   PB3 "run"   PB4 "+"/"-" (ADC2)
 *
 * States: ready (M:SS, "+"/"-" change it) -> counting down -> signal -> ready
 * at 2:00; a long press of "run" puts the device to deep sleep.
 * While the signal plays Timer0 is switched to tone generation on OC0B. */
#include "oled.h"
#include "timebase.h"

/* ---- settings (override on the make command line) ----------------------- */
#ifndef TONE_HZ
#define TONE_HZ 2000 /* 500..4000; pick the loudest with the tone test    */
#endif
#ifndef BEEP_MS
#define BEEP_MS 1000 /* length of the end-of-countdown signal             */
#endif
#define DEFAULT_MIN 2
#define MIN_MIN 1    /* lowest settable time, minutes (1:00); max is 60:00 */
/* OSCCAL_VAL: oscillator calibration found with the calib program. */

#if FEATURE_BAR
NOINIT static uint16_t total;   /* set time in seconds                     */
NOINIT static int16_t q, r;     /* progress bar: bar_lit = q + 1           */
#endif

/* Decrement the decimal number whose last digit is txt[i]; digits are
 * m10 m1 : s10 s1 (indices 0 1 . 3 4), seconds roll over at 59. */
static void dec(uint8_t i)
{
    while (!txt[i]) {
        txt[i] = (i == 3) ? 5 : 9;
        i = (i == 3) ? 1 : i - 1;
    }
    txt[i]--;
}

static void ready(void) /* 2:00, full frame, waiting for "run" */
{
    running = 0;
    txt[0] = 0;
    txt[1] = DEFAULT_MIN;
    txt[2] = GLYPH_COLON;
    txt[3] = 0;
    txt[4] = 0;
#if FEATURE_BAR
    bar_lit = BAR_PIXELS;
#endif
    oled_draw();
}

static void beep(void)
{
    TIMSK0 = 0;
    OCR0A = TONE_TOP(TONE_HZ);
    TCNT0 = 0;
    TCCR0B = CS_TONE;
    TCCR0A = (1 << COM0B0) | (1 << WGM01); /* toggle OC0B on compare (OCR0B=0) */
    delay_ms(BEEP_MS);
    timer_tick(); /* also disconnects OC0B: the pin falls back to PORTB1 = 0 */
}

/* Display off, everything off, power-down until "run" is pressed. */
static void sleep_now(void)
{
    oled_off();
    wait_release();
    TIMSK0 = 0;       /* no tick ISR while we wait for the wake-up press */
    ADCSRA = 0;       /* ADC off                                         */
    PCMSK = 1 << PCINT3;
    GIMSK = 1 << PCIE;
    snooze(1 << SM1); /* power-down */
    GIMSK = 0;
    wait_release();   /* the wake-up press must not start the timer */
}

int main(void)
{
    uint8_t e;

#ifdef OSCCAL_VAL
    OSCCAL = OSCCAL_VAL;
#endif
    for (;;) {                          /* (re)start: power-on and wake-up */
        hw_init();
        delay_ms(100);                  /* OLED power-up                   */
        oled_init();
        ready();
        ev = 0;

        for (;;) {
            wait_event();
            e = ev;
            ev = 0;
#ifdef AUTO_SLEEP_S
            mark = secs;
#endif

            if (e == B_LONG) {
                break;
            } else if (e == B_RUN) {
                if (running) {
                    ready();            /* stop (not pause) -> 2:00        */
                } else {
                    running = 1;
#if FEATURE_BAR
                    {
                        uint8_t m = (txt[0] << 3) + (txt[0] << 1) + txt[1];
                        total = (m << 6) - (m << 2);   /* minutes * 60 */
                    }
                    q = BAR_PIXELS - 1;
                    r = total - 1;
#endif
                    cli();              /* first second starts now         */
                    TCNT0 = 0;
                    tick = 0;
                    seen = secs;
                    sei();
                }
            } else if (e) {             /* "+" or "-", only when not running */
                if (!running) {
                    if (e == B_PLUS) {
                        if (txt[0] < 6) {
                            if (++txt[1] == 10) {
                                txt[1] = 0;
                                txt[0]++;
                            }
                        }
                    } else if (txt[0] || txt[1] > MIN_MIN) {
                        dec(1);
                    }
                    oled_draw();
                }
            } else {                    /* one more second elapsed         */
                seen++;
                dec(4);
#if FEATURE_BAR
                r -= BAR_PIXELS;
                while (r < 0) {
                    r += total;
                    q--;
                }
                bar_lit = q + 1;
#endif
                if (txt[0] | txt[1] | txt[3] | txt[4]) {
                    oled_draw();
                } else {                /* 0:00 reached: signal            */
#if FEATURE_BELL
                    bell = 1;
#endif
                    oled_draw();
                    beep();
#if FEATURE_BELL
                    bell = 0;
#endif
                    ready();
                    ev = 0;
                }
            }
        }

        sleep_now();
    }
}
