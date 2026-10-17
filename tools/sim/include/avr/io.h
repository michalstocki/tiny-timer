/* Host mock of <avr/io.h> for ATtiny13A: registers are objects with write
 * hooks, so that the real firmware sources run unmodified on the PC.
 * See tools/sim/sim.cpp. */
#pragma once
#include <stdint.h>
#define __AVR_ATtiny13A__ 1

enum { PB0, PB1, PB2, PB3, PB4, PB5 };
enum { ADLAR = 5, ADEN = 7, ADSC = 6, ADATE = 5 };
enum { COM0B0 = 4, WGM01 = 1, CS02 = 2, CS01 = 1, CS00 = 0 };
enum { OCIE0A = 2, OCF0A = 2 };
enum { SE = 5, SM1 = 4, SM0 = 3 };
enum { PCIE = 5, PCIF = 5, PCINT3 = 3 };

struct Reg {
    uint8_t v;
    void (*on_write)(uint8_t oldv, uint8_t newv);
    uint8_t (*on_read)(void);
    operator uint8_t() const { return on_read ? on_read() : v; }
    Reg &operator=(int x) {
        uint8_t o = v;
        v = (uint8_t)x;
        if (on_write) on_write(o, v);
        return *this;
    }
    Reg &operator|=(int x) { return *this = (uint8_t)((uint8_t)*this | x); }
    Reg &operator&=(int x) { return *this = (uint8_t)((uint8_t)*this & x); }
};

struct Regs {
    Reg DDRB, PORTB, PINB, ADMUX, ADCSRA, ADCH, TCCR0A, TCCR0B, OCR0A, OCR0B,
        TCNT0, TIMSK0, TIFR0, MCUCR, GIMSK, GIFR, PCMSK, OSCCAL, SREG_I;
};
extern Regs R;
#include "regs_macros.h"

#ifndef F_CPU
#define F_CPU 9600000UL
#endif
