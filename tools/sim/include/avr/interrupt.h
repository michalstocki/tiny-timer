#pragma once
#include <avr/io.h>
#define sei() (R.SREG_I = 1)
#define cli() (R.SREG_I = 0)
#define ISR(vect) extern "C" void vect(void); extern "C" void vect(void)
#define EMPTY_INTERRUPT(vect) extern "C" void vect(void); extern "C" void vect(void) {}
