/* Shared time base and button engine (included by main.c and calib.c).
 *
 * Timer0 runs an 8 ms tick (ATtiny13A: 9.6 MHz / 1024 / 75; ATtiny25/45/85,
 * "plan B": 8 MHz / 256 / 250 -- both exactly 125 ticks per second); the
 * ISR counts whole ticks, so there is no drift beyond the RC oscillator
 * error. It also decodes the three buttons:
 *   "run"  PB3 to GND (internal pull-up)
 *   "+"/"-" PB4 = ADC2, resistor ladder, free running 8 bit ADC
 * Hot variables live in registers (build with -ffixed-r2..r9): cheaper
 * access, and the ISR does not need to save anything. */
#ifndef TIMEBASE_H
#define TIMEBASE_H

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

#ifdef __AVR__
#define HOTVAR(name, reg) register uint8_t name asm(reg)
/* Registers modified by the ISR are not "volatile" to the compiler: this
 * empty asm tells it that the register may have changed behind its back. */
#define REFRESH(v) __asm__ volatile("" : "+r"(v))
#define CPU_SLEEP() __asm__ volatile("sei\n\tsleep" ::: "memory")
#else /* host simulation (tools/sim) */
#define HOTVAR(name, reg) static uint8_t name
#define REFRESH(v) ((void)0)
extern "C" void sim_sleep(void);
#define CPU_SLEEP() sim_sleep()
#endif

#define DEBOUNCE_TICKS 3   /* x 8 ms = 24 ms                              */
#define LONG_TICKS 250     /* x 8 ms = 2 s: long press of "run"           */
#define TICKS_PER_SEC 125

#if defined(__AVR_ATtiny13A__) || defined(__AVR_ATtiny13__)
#define TICK_VECT TIM0_COMPA_vect
#define TICK_TOP (75 - 1)                   /* clk/1024: 9375 Hz, 75 counts = 8 ms */
#define CS_TICK ((1 << CS02) | (1 << CS00)) /* clk/1024 */
#else /* ATtiny25/45/85 */
#define TICK_VECT TIMER0_COMPA_vect
#define TICK_TOP (250 - 1)                  /* clk/256: 31250 Hz, 250 counts = 8 ms */
#define CS_TICK (1 << CS02)                 /* clk/256 */
#ifndef TIMSK0
#define TIMSK0 TIMSK                        /* register is called TIMSK here */
#define TIFR0 TIFR
#endif
#endif
#define CS_TONE ((1 << CS01) | (1 << CS00)) /* clk/64   */
/* Tone: Timer0 CTC, OC0B toggles every OCR0A+1 counts of clk/64, so
 * f = F_CPU / 128 / (OCR0A + 1). */
#define TONE_TOP(hz) ((uint8_t)((F_CPU / 128 + (hz) / 2) / (hz) - 1))

/* Button codes (raw readout and events). */
enum { B_NONE, B_RUN, B_PLUS, B_MINUS, B_LONG };

HOTVAR(tick, "r2"); /* 0..124                               */
HOTVAR(secs, "r3"); /* free running seconds counter         */
HOTVAR(ev, "r4");   /* last button event, cleared by main   */
HOTVAR(last, "r5"); /* ISR: previous raw button code        */
HOTVAR(held, "r6"); /* ISR: "run" is pressed (debounced)    */
HOTVAR(cnt, "r7");  /* ISR: ticks the raw code is stable    */
HOTVAR(running, "r8");
HOTVAR(seen, "r9"); /* seconds already handled by main      */
#ifdef AUTO_SLEEP_S
HOTVAR(mark, "r10"); /* secs at the last user activity      */
#endif

ISR(TICK_VECT)
{
    uint8_t raw = B_RUN, v = ADCH; /* ADC2, left adjusted: 0..255 = 0..VCC */

    if (++tick == TICKS_PER_SEC) {
        tick = 0;
        secs++;
    }
    if (PINB & (1 << PB3))
        raw = v < 64 ? B_PLUS : v < 192 ? B_MINUS : B_NONE;

    if (raw != last) {
        last = raw;
        cnt = 0;
    } else if (cnt < LONG_TICKS) {
        cnt++;
        if (cnt == DEBOUNCE_TICKS) {
            if (raw == B_RUN)
                held = 1;               /* "run" acts on release */
            else if (raw)
                ev = raw;               /* "+" / "-" act on press */
            else if (held) {
                ev = B_RUN;
                held = 0;
            }
        } else if (cnt == LONG_TICKS && raw == B_RUN) {
            ev = B_LONG;
            held = 0;
        }
    }
}

EMPTY_INTERRUPT(PCINT0_vect)

static void __attribute__((noinline)) delay_ms(uint16_t n)
{
    while (n--)
        _delay_ms(1);
}

/* Timer0: 8 ms CTC tick, OC0B disconnected. */
static void __attribute__((noinline)) timer_tick(void)
{
    TCCR0A = 1 << WGM01;
    OCR0A = TICK_TOP;
    TCCR0B = CS_TICK;
    TIMSK0 = 1 << OCIE0A;
}

/* Pins, ADC and tick timer; call once after reset / wake-up. */
static void hw_init(void)
{
    DDRB = 1 << PB1;                /* speaker pin low output; SDA/SCL released */
    PORTB = 1 << PB3;               /* pull-up on "run"                */
    ADMUX = (1 << ADLAR) | 2;       /* ADC2, VCC reference, 8 bit      */
    ADCSRA = (1 << ADEN) | (1 << ADSC) | (1 << ADATE) | 7; /* free running, /128 */
    timer_tick();
    sei();
}

/* Sleep in the given mode (MCUCR SM bits) until an interrupt. */
static void snooze(uint8_t mode)
{
    MCUCR = mode | (1 << SE);
    CPU_SLEEP();
    MCUCR = 0;
}

/* Idle until a button event (or, if running, a new second). */
static void wait_event(void)
{
    for (;;) {
        REFRESH(ev);
        REFRESH(secs);
        if (ev || (running && seen != secs))
            return;
#ifdef AUTO_SLEEP_S
        if (!running && (uint8_t)(secs - mark) >= AUTO_SLEEP_S) {
            ev = B_LONG;                /* idle too long: go to sleep      */
            return;
        }
#endif
        snooze(0);                  /* until the next 8 ms tick        */
    }
}

/* Wait until "run" has been released for 30 ms in a row (contact bounce). */
static void __attribute__((noinline, unused)) wait_release(void)
{
    uint8_t n = 0;
    while (n < 30) {
        delay_ms(1);
        n = (PINB & (1 << PB3)) ? n + 1 : 0;
    }
}

#endif
