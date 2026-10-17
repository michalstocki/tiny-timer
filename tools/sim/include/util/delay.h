#pragma once
extern "C" void sim_delay_us(double us);
static inline void _delay_ms(double ms) { sim_delay_us(ms * 1000.0); }
